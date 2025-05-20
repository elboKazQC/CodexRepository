import * as vscode from 'vscode';
import axios from 'axios';

/**
 * Classe pour analyser les logs et configurations des appareils Moxa
 */
export default class MoxaAnalyzer {
    private apiKey: string;
    private model: string;
    private apiBaseUrl: string;
    private idealConfig: any;

    constructor() {
        // Récupérer la clé API depuis les variables d'environnement ou les paramètres de l'extension
        this.apiKey = process.env.OPENAI_API_KEY || vscode.workspace.getConfiguration('moxaWifiAnalyzer').get('openaiApiKey') || '';
        if (!this.apiKey) {
            throw new Error('La clé API OpenAI n\'est pas configurée. Veuillez la définir dans le fichier .env ou dans les paramètres de l\'extension.');
        }
        
        this.model = "gpt-4"; // Modèle par défaut
        this.apiBaseUrl = "https://api.openai.com/v1/chat/completions";
        
        // Paramètres idéaux pour la configuration Moxa
        this.idealConfig = {
            'min_transmission_rate': 12,
            'max_transmission_power': 20,
            'rts_threshold': 512,
            'fragmentation_threshold': 2346,
            'roaming_mechanism': 'snr',
            'roaming_difference': 8,
            'remote_connection_check': true,
            'wmm_enabled': true,
            'turbo_roaming': true,
            'ap_alive_check': true,
            'roaming_threshold_type': 'snr',
            'roaming_threshold_value': 40,  // SNR en dB, ou -75 en dBm si type est 'signal_strength'
            'ap_candidate_threshold_type': 'snr',
            'ap_candidate_threshold_value': 25,  // SNR en dB, ou -75 en dBm si type est 'signal_strength'
        };
    }

    /**
     * Définit la clé API pour le service d'IA
     * @param apiKey - Clé API OpenAI
     */
    public setApiKey(apiKey: string): void {
        this.apiKey = apiKey;
        // Enregistrer la clé dans les paramètres de l'extension
        vscode.workspace.getConfiguration('moxaWifiAnalyzer').update('openaiApiKey', apiKey, vscode.ConfigurationTarget.Global);
    }

    /**
     * Analyse les logs Moxa avec l'IA et génère des recommandations
     * @param logContent - Contenu du log Moxa
     * @param currentConfig - Configuration actuelle du Moxa
     * @returns Résultats de l'analyse
     */
    public async analyzeLog(logContent: string, currentConfig: any): Promise<any> {
        if (!this.apiKey) {
            // Si pas de clé API, demander à l'utilisateur
            const apiKey = await vscode.window.showInputBox({
                prompt: 'Veuillez entrer votre clé API OpenAI',
                password: true,
                ignoreFocusOut: true
            });
            
            if (!apiKey) {
                throw new Error("Aucune clé API fournie. L'analyse ne peut pas continuer.");
            }
            
            this.setApiKey(apiKey);
        }
        
        vscode.window.showInformationMessage("Analyse du log avec l'IA en cours...");
        
        // Tronquer le log si trop volumineux
        const max_log_length = 15000;  // Limite pour éviter des coûts API trop élevés
        let truncatedLog = logContent;
        if (logContent.length > max_log_length) {
            truncatedLog = logContent.substring(0, max_log_length) + "\n[Log tronqué pour limiter la taille...]";
            vscode.window.showWarningMessage(`Log tronqué de ${logContent.length} à ${max_log_length} caractères pour l'analyse IA.`);
        }
        
        // Créer le prompt pour l'IA
        const prompt = this._createAnalysisPrompt(truncatedLog, currentConfig);
        
        // Appeler l'API IA
        const aiResponse = await this._callAiApi(prompt);
        
        if (!aiResponse) {
            throw new Error("Aucune réponse de l'API IA");
        }
        
        // Traiter la réponse de l'IA
        return this._processAiResponse(aiResponse, currentConfig);
    }

    /**
     * Crée le prompt pour l'analyse IA
     * @param logContent - Contenu du log Moxa
     * @param currentConfig - Configuration actuelle du Moxa
     * @returns Prompt pour l'API IA
     */
    private _createAnalysisPrompt(logContent: string, currentConfig: any): string {
        // Convertir la configuration actuelle en texte formaté
        const configText = JSON.stringify(currentConfig, null, 2);
        
        // Créer le prompt avec instructions spécifiques pour l'IA
        return `En tant qu'expert en réseaux sans fil et particulièrement en configuration d'appareils Moxa, analysez le log suivant et la configuration actuelle pour fournir des recommandations d'optimisation du roaming.

## Configuration actuelle du Moxa:
\`\`\`json
${configText}
\`\`\`

## Objectifs de l'analyse:
1. Identifier les événements de roaming dans le log
2. Analyser les performances de roaming (temps de basculement, amélioration du SNR, etc.)
3. Évaluer si les paramètres actuels sont optimaux
4. Suggérer des modifications pour améliorer les performances de roaming
5. Fournir des recommandations personnalisées pour le cas spécifique

## Log Moxa à analyser:
\`\`\`
${logContent}
\`\`\`

## Paramètres idéaux pour référence:
- Taux de transmission min: 12 Mbps (améliore la fiabilité des transmissions)
- Puissance max: 20 dBm (équilibre entre portée et interférences)
- Seuil RTS: 512 (idéal pour environnements industriels avec interférences)
- Seuil de fragmentation: 2346 (évite la fragmentation inutile)
- Mécanisme de roaming: SNR (plus fiable que la force du signal)
- Différence de roaming: 8 dB (bon équilibre pour éviter l'effet ping-pong)
- Seuil de roaming (SNR): 40 dB (idéal pour environnements industriels)
- Seuil de roaming (Signal Strength): -75 dBm (idéal pour environnements industriels) 
- Seuil candidat AP (SNR): 25 dB (permet une bonne sélection d'AP)
- Seuil candidat AP (Signal Strength): -75 dBm (permet une bonne sélection d'AP)
- Vérification de connexion distante: Activée (améliore la détection des déconnexions)
- WMM: Activé (améliore la QoS)
- Turbo Roaming: Activé (réduit le temps de basculement)
- AP alive check: Activé (améliore la fiabilité)

## Format de réponse demandé (JSON):
\`\`\`json
{
  "roaming_metrics": {
    "total_events": 0,
    "avg_handoff_time": 0,
    "min_handoff_time": 0,
    "max_handoff_time": 0,
    "avg_snr_before": 0,
    "avg_snr_after": 0,
    "snr_improvement": 0
  },
  "score": 0,
  "recommendations": [
    "Description détaillée de la recommandation 1 avec des actions concrètes",
    "Description détaillée de la recommandation 2 avec des actions concrètes"
  ],
  "config_changes": [
    {
      "param": "Nom du paramètre",
      "current": "Valeur actuelle",
      "recommended": "Valeur recommandée",
      "reason": "Raison détaillée du changement",
      "impact": "Impact attendu du changement sur les performances"
    }
  ],
  "analysis": "Analyse détaillée des performances de roaming, expliquant les problèmes identifiés et comment les changements recommandés les résoudront"
}
\`\`\`

Pour chaque recommandation, fournir:
1. Une explication détaillée du problème identifié
2. Les actions concrètes à entreprendre
3. Les bénéfices attendus après le changement
4. Des conseils pour évaluer l'efficacité du changement

Fournissez votre réponse uniquement au format JSON demandé, sans texte supplémentaire.
`;
    }

    /**
     * Appelle l'API IA avec le prompt
     * @param prompt - Prompt pour l'IA
     * @returns Réponse de l'IA
     */
    private async _callAiApi(prompt: string): Promise<string | null> {
        try {
            const response = await axios.post(
                this.apiBaseUrl,
                {
                    model: this.model,
                    messages: [{ role: "user", content: prompt }],
                    temperature: 0.2,  // Valeur basse pour des réponses plus cohérentes
                    max_tokens: 4000
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.apiKey}`
                    },
                    timeout: 60000  // 60 secondes de timeout
                }
            );
            
            if (response.status === 200) {
                return response.data.choices[0].message.content;
            } else {
                vscode.window.showErrorMessage(`Erreur API (${response.status}): ${response.statusText}`);
                return null;
            }
        } catch (error: any) {
            if (error.response) {
                vscode.window.showErrorMessage(`Erreur API (${error.response.status}): ${error.response.data.error.message}`);
            } else {
                vscode.window.showErrorMessage(`Erreur lors de l'appel API: ${error.message}`);
            }
            return null;
        }
    }

    /**
     * Traite la réponse de l'IA et génère le rapport final
     * @param aiResponse - Réponse de l'IA
     * @param currentConfig - Configuration actuelle
     * @returns Résultats formatés
     */
    private _processAiResponse(aiResponse: string, currentConfig: any): any {
        try {
            // Extraire le JSON de la réponse (peut contenir du texte supplémentaire)
            const jsonStart = aiResponse.indexOf('{');
            const jsonEnd = aiResponse.lastIndexOf('}') + 1;
            
            let aiResults;
            if (jsonStart >= 0 && jsonEnd > jsonStart) {
                const jsonResponse = aiResponse.substring(jsonStart, jsonEnd);
                aiResults = JSON.parse(jsonResponse);
            } else {
                // Essayer de parser directement si aucun JSON n'est trouvé
                aiResults = JSON.parse(aiResponse);
            }
            
            // Structure de base pour les résultats
            const results: any = {
                score: 0,
                max_score: 100,
                roaming_metrics: {},
                recommendations: [],
                config_changes: [],
                ai_insights: "",
                current_config: currentConfig,
                timestamp: new Date().toISOString()
            };
            
            // Extraction des scores
            if ('score' in aiResults) {
                try {
                    results.score = parseInt(aiResults.score, 10) || 0;
                } catch (error) {
                    // Si le score n'est pas un nombre, on utilise 0
                    results.score = 0;
                }
            }
            
            // Extraction des métriques de roaming avec valeurs par défaut
            const roaming_metrics = aiResults.roaming_metrics || {};
            if (roaming_metrics) {
                const default_metrics = {
                    total_events: 0,
                    avg_handoff_time: 0,
                    min_handoff_time: 0,
                    max_handoff_time: 0,
                    avg_snr_before: 0,
                    avg_snr_after: 0,
                    snr_improvement: 0
                };
                
                // S'assurer que toutes les métriques existent
                for (const [key, defaultValue] of Object.entries(default_metrics)) {
                    if (!(key in roaming_metrics) || roaming_metrics[key] === null) {
                        roaming_metrics[key] = defaultValue;
                    } else if (typeof roaming_metrics[key] !== 'number') {
                        try {
                            roaming_metrics[key] = parseFloat(roaming_metrics[key]);
                        } catch (error) {
                            roaming_metrics[key] = defaultValue;
                        }
                    }
                }
                
                results.roaming_metrics = roaming_metrics;
            }
            
            // Extraction des recommandations
            if ('recommendations' in aiResults && Array.isArray(aiResults.recommendations)) {
                results.recommendations = aiResults.recommendations;
            }
            
            // Extraction des changements de configuration
            if ('config_changes' in aiResults && Array.isArray(aiResults.config_changes)) {
                results.config_changes = aiResults.config_changes;
            }
            
            // Extraction des insights (analyse détaillée)
            if ('analysis' in aiResults) {
                results.ai_insights = aiResults.analysis;
            }
            
            // Calculer le statut global
            const score_percent = (results.score / results.max_score) * 100;
            if (score_percent >= 80) {
                results.status = "EXCELLENT";
            } else if (score_percent >= 60) {
                results.status = "PASSABLE";
            } else {
                results.status = "INSUFFISANT";
            }
            
            return results;
            
        } catch (error: any) {
            vscode.window.showErrorMessage(`Erreur lors du traitement de la réponse IA: ${error.message}`);
            
            // Retourner un résultat minimal en cas d'échec
            return {
                score: 0,
                max_score: 100,
                status: "ERREUR",
                error_message: `Impossible de traiter la réponse de l'IA: ${error.message}`,
                raw_response: aiResponse,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Génère un rapport formaté en texte lisible
     * @param results - Résultats de l'analyse
     * @returns Rapport formaté
     */
    public getUserFriendlyReport(results: any): string {
        if (!results || !results.score) {
            return "Aucune analyse disponible.";
        }
        
        // Calcul du score en pourcentage
        const score_percent = Math.round((results.score / results.max_score) * 100);
        const status = results.status || "INCONNU";
        
        // Créer le rapport
        const report = [];
        report.push("=" + "=".repeat(59));
        report.push(`RAPPORT D'ANALYSE MOXA IA - ${results.timestamp || 'Date inconnue'}`);
        report.push("=" + "=".repeat(59));
        
        report.push(`\nSCORE GLOBAL: ${score_percent}% - ${status}`);
        
        // Métriques de roaming
        const metrics = results.roaming_metrics || {};
        if (metrics) {
            report.push("\n--- MÉTRIQUES DE ROAMING ---");
            report.push(`Événements de roaming: ${metrics.total_events || 0}`);
            report.push(`Temps de basculement moyen: ${metrics.avg_handoff_time || 0} ms`);
            report.push(`Temps min/max: ${metrics.min_handoff_time || 0} / ${metrics.max_handoff_time || 0} ms`);
            report.push(`SNR moyen avant roaming: ${metrics.avg_snr_before || 0} dB`);
            report.push(`SNR moyen après roaming: ${metrics.avg_snr_after || 0} dB`);
            report.push(`Amélioration moyenne du SNR: ${metrics.snr_improvement || 0} dB`);
        }
        
        // Recommandations
        const recommendations = results.recommendations || [];
        if (recommendations.length > 0) {
            report.push("\n--- RECOMMANDATIONS ---");
            recommendations.forEach((rec: string, i: number) => {
                report.push(`${i + 1}. ${rec}`);
            });
        }
        
        // Changements de configuration
        const config_changes = results.config_changes || [];
        if (config_changes.length > 0) {
            report.push("\n--- CHANGEMENTS DE CONFIGURATION RECOMMANDÉS ---");
            config_changes.forEach((change: any, i: number) => {
                report.push(`${i + 1}. Modifier '${change.param || ''}':`);
                report.push(`   - De: ${change.current || ''}`);
                report.push(`   - À:  ${change.recommended || ''}`);
                report.push(`   - Raison: ${change.reason || ''}`);
                if (change.impact) {
                    report.push(`   - Impact: ${change.impact}`);
                }
            });
        }
        
        // Analyse détaillée
        const insights = results.ai_insights || "";
        if (insights) {
            report.push("\n--- ANALYSE DÉTAILLÉE ---");
            report.push(insights);
        }
        
        report.push("\n" + "=".repeat(60));
        report.push("Fin du rapport d'analyse IA");
        
        return report.join("\n");
    }
}
