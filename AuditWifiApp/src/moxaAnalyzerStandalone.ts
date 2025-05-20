import axios from 'axios';
import * as dotenv from 'dotenv';

// Charger les variables d'environnement
dotenv.config();

class MoxaAnalyzerStandalone {
    private apiKey: string;
    private model: string;
    private apiBaseUrl: string;
    private idealConfig: any;

    constructor() {
        this.apiKey = process.env.OPENAI_API_KEY || '';
        if (!this.apiKey) {
            throw new Error('La clé API OpenAI n\'est pas configurée. Veuillez la définir dans le fichier .env.');
        }
        
        this.model = "gpt-4";
        this.apiBaseUrl = "https://api.openai.com/v1/chat/completions";
        
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
            'roaming_threshold_value': 40,
            'ap_candidate_threshold_type': 'snr',
            'ap_candidate_threshold_value': 25,
        };
    }

    public async analyzeLog(logContent: string, currentConfig: any): Promise<any> {
        console.log("Analyse du log avec l'IA en cours...");
        
        const max_log_length = 15000;
        let truncatedLog = logContent;
        if (logContent.length > max_log_length) {
            truncatedLog = logContent.substring(0, max_log_length) + "\n[Log tronqué pour limiter la taille...]";
            console.log(`Log tronqué de ${logContent.length} à ${max_log_length} caractères pour l'analyse IA.`);
        }
        
        const prompt = this._createAnalysisPrompt(truncatedLog, currentConfig);
        const aiResponse = await this._callAiApi(prompt);
        
        if (!aiResponse) {
            throw new Error("Aucune réponse de l'API IA");
        }
        
        return this._processAiResponse(aiResponse, currentConfig);
    }

    private _createAnalysisPrompt(logContent: string, currentConfig: any): string {
        const configText = JSON.stringify(currentConfig, null, 2);
        return `En tant qu'expert en réseaux sans fil et particulièrement en configuration d'appareils Moxa, analysez le log suivant et la configuration actuelle pour fournir des recommandations d'optimisation du roaming.

## Configuration actuelle du Moxa:
\`\`\`json
${configText}
\`\`\`

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

Analysez les éléments suivants dans le log:
1. Nombre total d'événements de roaming
2. Temps moyen de handoff
3. Amélioration moyenne du SNR après roaming
4. Stabilité des connexions
5. Efficacité des paramètres actuels

Fournissez une réponse au format JSON avec:
1. Métriques de performance
2. Score global sur 100
3. Recommandations spécifiques
4. Changements de configuration suggérés

Format de réponse JSON attendu:
{
  "roaming_metrics": {
    "total_events": X,
    "avg_handoff_time": X,
    "min_handoff_time": X,
    "max_handoff_time": X,
    "avg_snr_before": X,
    "avg_snr_after": X,
    "snr_improvement": X
  },
  "score": X,
  "recommendations": [
    "Recommandation détaillée 1",
    "Recommandation détaillée 2"
  ],
  "config_changes": [
    {
      "param": "nom_parametre",
      "current": "valeur_actuelle",
      "recommended": "valeur_recommandee",
      "reason": "raison_du_changement"
    }
  ],
  "analysis": "Analyse détaillée des performances"
}`;
    }

    private async _callAiApi(prompt: string): Promise<string | null> {
        try {
            const response = await axios.post(
                this.apiBaseUrl,
                {
                    model: this.model,
                    messages: [{ role: "user", content: prompt }],
                    temperature: 0.2,
                    max_tokens: 4000
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.apiKey}`
                    },
                    timeout: 60000
                }
            );
              if (response.status === 200 && response.data.choices && response.data.choices[0]) {
                console.log('Réponse brute de l\'API:', response.data.choices[0].message.content);
                return response.data.choices[0].message.content;
            }
            console.error('Réponse invalide de l\'API:', response.data);
            return null;
        } catch (error: any) {
            console.error('Erreur API:', error.message);
            if (error.response) {
                console.error('Détails:', error.response.data);
            }
            throw error;
        }
    }    private _processAiResponse(aiResponse: string, currentConfig: any): any {
        try {
            console.log('Traitement de la réponse...');
            
            // Recherche du JSON dans la réponse
            const jsonStart = aiResponse.indexOf('{');
            const jsonEnd = aiResponse.lastIndexOf('}') + 1;
            
            let aiResults;
            if (jsonStart >= 0 && jsonEnd > jsonStart) {
                const jsonResponse = aiResponse.substring(jsonStart, jsonEnd);
                console.log('JSON extrait:', jsonResponse);
                try {
                    aiResults = JSON.parse(jsonResponse);
                } catch (parseError) {
                    console.error('Erreur de parsing JSON:', parseError);
                    console.log('Tentative de nettoyage du JSON...');
                    // Tentative de nettoyage du JSON
                    const cleanedJson = jsonResponse.replace(/\\n/g, ' ').replace(/\s+/g, ' ');
                    aiResults = JSON.parse(cleanedJson);
                }
            } else {
                console.log('Pas de JSON trouvé, tentative de parse direct...');
                aiResults = JSON.parse(aiResponse);
            }
            
            return {
                score: aiResults.score || 0,
                max_score: 100,
                roaming_metrics: aiResults.roaming_metrics || {},
                recommendations: aiResults.recommendations || [],
                config_changes: aiResults.config_changes || [],
                analysis: aiResults.analysis || "",
                current_config: currentConfig,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('Erreur lors du traitement de la réponse:', error);
            throw error;
        }
    }
}

export { MoxaAnalyzerStandalone };
