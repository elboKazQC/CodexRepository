"""
Convertit les résultats d'analyse au format JSON en un format conversationnel
semblable à une réponse de ChatGPT, pour une lecture plus fluide et naturelle.
"""
from datetime import datetime

from datetime import datetime

def format_conversationally(analysis_results):
    """
    Transforme les résultats d'analyse JSON en un texte conversationnel.
    
    Args:
        analysis_results (dict): Résultats de l'analyse au format JSON
        
    Returns:
        str: Texte formaté de manière conversationnelle
    """
    if not analysis_results or not isinstance(analysis_results, dict):
        return "Je n'ai pas pu analyser les logs fournis. Veuillez vérifier le format des données."
    
    # Vérifier s'il y a une erreur dans l'analyse
    if 'error' in analysis_results:
        error_msg = analysis_results.get('error', 'Erreur inconnue')
        return f"# Erreur lors de l'analyse\n\nJe n'ai pas pu analyser les logs fournis en raison de l'erreur suivante :\n\n```\n{error_msg}\n```\n\n**Recommandation** : Vérifiez le format des logs et assurez-vous qu'ils contiennent des informations pertinentes pour l'analyse."
    
    # On extrait l'analyse principale qui peut être sous différentes clés
    if 'raw_response' in analysis_results:
        # Les résultats WiFi passent généralement par ce champ
        analysis = analysis_results.get('raw_response', {})
    else:
        # Sinon on utilise directement les résultats
        analysis = analysis_results
    
    # Détermine le type d'analyse (Moxa ou WiFi standard)
    is_moxa = any(key in analysis for key in ['roaming_metrics', 'ping_pong']) or analysis_results.get('is_moxa_log', False)
    
    # Début du message
    message = []
    if is_moxa:
        message.append("# Rapport d'analyse des logs Moxa\n")
        message.append(f"*Analyse réalisée le {datetime.now().strftime('%d-%m-%Y à %H:%M')}*\n")
    else:
        message.append("# Rapport d'analyse WiFi\n")
        message.append(f"*Analyse réalisée le {datetime.now().strftime('%d-%m-%Y à %H:%M')}*\n")
      # Score et évaluation générale - utiliser uniquement ce que OpenAI a déterminé
    score = analysis.get('score_global', analysis.get('score', 0))
    # Délégation complète de l'évaluation à OpenAI, nous affichons simplement le score
    message.append(f"📊 **Score global: {score}/100**\n")
    
    # Récupération des éléments clés selon le type d'analyse
    if is_moxa:
        message.append(_format_moxa_analysis(analysis, analysis_results.get('current_config', {})))
    else:
        message.append(_format_wifi_analysis(analysis))
    
    # Section recommandations
    recommendations = analysis.get('recommandations', analysis.get('recommendations', []))
    if recommendations:
        message.append("\n## 🛠️ Recommandations\n")
        
        if isinstance(recommendations, list):
            for i, rec in enumerate(recommendations, 1):
                if isinstance(rec, dict):
                    message.append(f"{i}. **{rec.get('probleme', 'Problème')}**")
                    message.append(f"   - Solution: {rec.get('solution', 'Non spécifiée')}")
                    
                    if 'priorite' in rec:
                        priority = rec.get('priorite', 3)
                        priority_label = "Haute" if priority >= 4 else "Moyenne" if priority >= 2 else "Basse"
                        message.append(f"   - Priorité: {priority_label}")
                    
                    if 'parametres' in rec and rec['parametres']:
                        message.append("   - Paramètres à modifier:")
                        for param, val in rec['parametres'].items():
                            message.append(f"     * `{param}`: {val}")
                    message.append("")
                else:
                    message.append(f"{i}. {rec}\n")
        elif isinstance(recommendations, dict):
            for problem, solution in recommendations.items():
                message.append(f"- **{problem}**: {solution}\n")
      # Conclusion - utilisons maintenant celle fournie par l'analyse OpenAI si disponible
    message.append("\n## 🔍 Conclusion")
    
    conclusion = analysis.get('conclusion', None)
    if conclusion:
        if isinstance(conclusion, str):
            message.append(f"\n{conclusion}")
        elif isinstance(conclusion, list):
            for item in conclusion:
                message.append(f"\n- {item}")
    else:
        # Si pas de conclusion spécifique, utiliser une version générique basée sur le score
        if is_moxa:
            if score >= 80:
                message.append("\nVotre configuration Moxa est robuste et répond bien aux besoins actuels des AMRs. Surveillez les métriques de performance du roaming régulièrement pour maintenir cette qualité.")
            elif score >= 60:
                message.append("\nVotre configuration Moxa fonctionne correctement mais présente des opportunités d'amélioration pour votre flotte d'AMRs. En appliquant les recommandations ci-dessus, vous pourriez observer des performances plus stables et une meilleure fiabilité des connexions WiFi pour vos robots.")
            else:
                message.append("\nVotre configuration Moxa nécessite des ajustements importants pour assurer une performance optimale de votre flotte d'AMRs. Je vous recommande d'implémenter les recommandations ci-dessus dès que possible pour résoudre les problèmes identifiés et améliorer significativement la stabilité et les performances de connexion.")
        else:
            if score >= 80:
                message.append("\nVotre configuration WiFi est robuste et répond bien aux besoins actuels. Surveillez les métriques de performance régulièrement pour maintenir cette qualité.")
            elif score >= 60:
                message.append("\nVotre configuration WiFi fonctionne correctement mais présente des opportunités d'amélioration. En appliquant les recommandations ci-dessus, vous pourriez observer des performances plus stables et une meilleure fiabilité.")
            else:
                message.append("\nVotre configuration WiFi nécessite des ajustements importants. Je vous recommande d'implémenter les recommandations ci-dessus dès que possible pour résoudre les problèmes identifiés et améliorer significativement la stabilité et les performances.")
    
    axes = analysis.get('axes_amelioration', analysis.get('axes_d_amelioration', []))
    if axes:
        message.append("\n**Principaux axes d'amélioration:**")
        if isinstance(axes, list):
            for axe in axes:
                message.append(f"- {axe}")
        else:
            message.append(f"- {axes}")
    
    # Note de bas de page
    if is_moxa:
        message.append("\n---\n*Rapport généré par l'Analyseur de Configuration Moxa Noovelia*")
    else:
        message.append("\n---\n*Rapport généré par l'Analyseur WiFi Noovelia*")
    
    return "\n".join(message)

def _format_moxa_analysis(analysis, current_config=None):
    """Format les résultats d'analyse spécifiques aux logs Moxa."""
    message = []
    
    message.append("\n## 📝 Résumé de l'analyse\n")
    
    # Adaptabilité pour les AMRs
    adapte = analysis.get('adapte_flotte_AMR', False)
    if adapte:
        message.append("✅ Cette configuration est **adaptée pour une flotte d'AMRs**.\n")
    else:
        message.append("⚠️ Cette configuration **n'est pas optimale pour une flotte d'AMRs** et nécessite des ajustements.\n")
      # Analyse de la configuration actuelle (si disponible) - Utiliser l'évaluation d'OpenAI
    if current_config:
        message.append("### Configuration Moxa actuelle")
        
        # Récupérer l'évaluation des paramètres depuis l'analyse d'OpenAI 
        # au lieu de faire l'évaluation localement
        config_evaluation = analysis.get('evaluation_configuration', {})
        config_params = analysis.get('parametres_actuels', analysis.get('details_configuration', {}).get('parametres_actuels', {}))
        
        # Afficher les paramètres clés avec leur évaluation provenant d'OpenAI
        turbo_roaming = current_config.get('turbo_roaming', False)
        roaming_diff = current_config.get('roaming_difference', 0)
        roaming_mech = current_config.get('roaming_mechanism', '')
        
        # Afficher simplement les valeurs et récupérer leur statut depuis l'analyse OpenAI
        turbo_status = "✅" if config_evaluation.get('turbo_roaming_correct', config_params.get('turbo_roaming_correct', False)) else "⚠️"
        message.append(f"{turbo_status} **Turbo Roaming**: {'Activé' if turbo_roaming else 'Désactivé'}")
        
        mech_status = "✅" if config_evaluation.get('roaming_mechanism_correct', config_params.get('roaming_mechanism_correct', False)) else "⚠️"
        message.append(f"{mech_status} **Mécanisme de Roaming**: {roaming_mech}")
        
        diff_status = "✅" if config_evaluation.get('roaming_difference_correct', config_params.get('roaming_difference_correct', False)) else "⚠️"
        message.append(f"{diff_status} **Différence de Roaming**: {roaming_diff}")
        
        message.append("")
    
    # Roaming metrics (spécifique à Moxa)
    roaming_metrics = analysis.get('roaming_metrics', {})
    if roaming_metrics:
        message.append("### Performances de roaming")
        
        # Temps moyen de roaming
        avg_time = roaming_metrics.get('temps_moyen_roaming_ms', 0)
        if avg_time > 0:
            if avg_time < 100:
                message.append(f"✅ **Temps moyen de roaming**: {avg_time} ms (excellent)")
            elif avg_time < 300:
                message.append(f"✅ **Temps moyen de roaming**: {avg_time} ms (bon)")
            else:
                message.append(f"⚠️ **Temps moyen de roaming**: {avg_time} ms (lent)")
        
        # Fréquence des roamings
        frequency = roaming_metrics.get('frequence_roaming', 0)
        if frequency > 0:
            if frequency > 10:
                message.append(f"⚠️ **Fréquence de roaming**: {frequency} roamings par minute (élevée)")
            else:
                message.append(f"✅ **Fréquence de roaming**: {frequency} roamings par minute (normale)")
        
        message.append("")
    
    # Problèmes détectés (analyse détaillée)
    if 'analyse_detaillee' in analysis:
        details = analysis['analyse_detaillee']
        
        # Effet ping-pong
        if 'ping_pong' in details:
            ping_pong = details['ping_pong']
            if ping_pong.get('detecte', False):
                message.append("### ⚠️ Effet Ping-Pong détecté")
                message.append(f"J'ai identifié un **effet ping-pong** entre certains points d'accès avec une gravité de {ping_pong.get('gravite', 'N/A')}/10.")
                
                if 'occurrences' in ping_pong and ping_pong['occurrences']:
                    if len(ping_pong['occurrences']) > 2:
                        message.append(f"Cela s'est produit {len(ping_pong['occurrences'])} fois, notamment entre:")
                        for i, occ in enumerate(ping_pong['occurrences'][:2]):
                            message.append(f"- {occ}")
                        message.append(f"- Et {len(ping_pong['occurrences'])-2} autres occurrences")
                    else:
                        message.append("Occurrences observées:")
                        for occ in ping_pong['occurrences']:
                            message.append(f"- {occ}")
                
                # Lien avec la configuration actuelle
                if current_config:
                    roaming_diff = current_config.get('roaming_difference', 0)
                    if roaming_diff < 8:
                        message.append("\n**Lien avec votre configuration**: Votre paramètre `roaming_difference` actuel de " +
                                    f"{roaming_diff} est probablement trop faible, ce qui contribue à l'effet ping-pong. " +
                                    "Une valeur entre 8 et 12 est généralement recommandée pour les AMRs.")
                
                message.append("\nCet effet ping-pong peut provoquer des déconnexions temporaires et affecter la stabilité de la connexion des AMRs en mouvement.")
                message.append("")
        
        # Problèmes SNR
        if 'problemes_snr' in details:
            snr = details['problemes_snr']
            if snr.get('aps_snr_zero', []):
                message.append("### ⚠️ Problèmes de rapport signal/bruit (SNR)")
                
                ap_count = len(snr.get('aps_snr_zero', []))
                message.append(f"J'ai détecté **{ap_count} points d'accès** avec des valeurs SNR critiques ou nulles:")
                
                # Limiter à 3 APs dans l'affichage pour ne pas surcharger
                for i, ap in enumerate(snr.get('aps_snr_zero', [])[:3]):
                    message.append(f"- {ap}")
                
                if ap_count > 3:
                    message.append(f"- Et {ap_count-3} autres points d'accès")
                
                # Lien avec la configuration actuelle
                if current_config:
                    roaming_threshold_type = current_config.get('roaming_threshold_type', '')
                    roaming_threshold_value = current_config.get('roaming_threshold_value', 0)
                    if roaming_threshold_type == "signal_strength" and roaming_threshold_value > -65:
                        message.append("\n**Lien avec votre configuration**: Votre seuil de roaming actuel de " +
                                    f"{roaming_threshold_value} dBm pourrait être trop élevé pour votre environnement. " +
                                    "Considérez une valeur entre -65 et -70 dBm pour un meilleur équilibre.")
                
                message.append("\nUn SNR faible ou nul indique une mauvaise qualité de réception du signal, ce qui peut causer des déconnexions fréquentes et des problèmes de performance.")
                message.append("")
        
        # Problèmes d'authentification
        if 'authentification' in details:
            auth = details['authentification']
            if auth.get('timeouts', 0) > 0 or auth.get('echecs', 0) > 0:
                message.append("### ⚠️ Problèmes d'authentification")
                
                timeout_count = auth.get('timeouts', 0)
                failure_count = auth.get('echecs', 0)
                avg_time = auth.get('temps_moyen_ms', 0)
                
                message.append(f"J'ai identifié des problèmes d'authentification dans vos logs:")
                message.append(f"- **{timeout_count}** timeouts d'authentification")
                message.append(f"- **{failure_count}** échecs d'authentification")
                
                if avg_time > 0:
                    if avg_time > 500:
                        message.append(f"- Temps moyen d'authentification: **{avg_time} ms** (lent)")
                    else:
                        message.append(f"- Temps moyen d'authentification: **{avg_time} ms**")
                
                # Lien avec la configuration actuelle
                if current_config:
                    remote_connection_check = current_config.get('remote_connection_check', False)
                    ap_alive_check = current_config.get('ap_alive_check', False)
                    
                    if not remote_connection_check or not ap_alive_check:
                        message.append("\n**Lien avec votre configuration**: Considérez d'activer à la fois " +
                                    "`remote_connection_check` et `ap_alive_check` pour améliorer la détection " +
                                    "précoce des problèmes de connexion et réduire les délais d'authentification.")
                
                message.append("\nCes problèmes peuvent causer des déconnexions et des délais dans l'établissement de nouvelles connexions pour vos AMRs.")
                message.append("")
    
    return "\n".join(message)

def _format_wifi_analysis(analysis):
    """Format les résultats d'analyse spécifiques aux logs WiFi standards."""
    message = []
    
    message.append("\n## 📝 Résumé de l'analyse\n")
    
    # Adaptabilité pour les AMRs
    adapte = analysis.get('adapte_flotte_AMR', analysis.get('adapte_pour_amr', False))
    if adapte:
        message.append("✅ Cette configuration est **adaptée pour une flotte d'AMRs**.\n")
    else:
        message.append("⚠️ Cette configuration **n'est pas optimale pour une flotte d'AMRs** et nécessite des ajustements.\n")
    
    # Analyse détaillée
    if 'analyse_detaillee' in analysis:
        details = analysis['analyse_detaillee']
        
        # Qualité du signal
        if 'signal' in details:
            signal = details['signal']
            message.append("### 📶 Qualité du signal")
            
            niveau = signal.get('niveau_moyen', 'N/A')
            message.append(f"**Niveau moyen du signal**: {niveau}")
            
            stabilite = signal.get('stabilite', 0)
            if stabilite >= 7:
                message.append(f"**Stabilité**: {stabilite}/10 (bonne)")
            elif stabilite >= 4:
                message.append(f"**Stabilité**: {stabilite}/10 (moyenne)")
            else:
                message.append(f"**Stabilité**: {stabilite}/10 (faible)")
            
            if 'zones_faibles' in signal and signal['zones_faibles']:
                message.append("\n**Zones de signal faible identifiées**:")
                for zone in signal['zones_faibles'][:3]:  # Limiter à 3 zones
                    message.append(f"- {zone}")
                
                if len(signal['zones_faibles']) > 3:
                    message.append(f"- Et {len(signal['zones_faibles'])-3} autres zones")
            
            message.append("")
        
        # Problèmes de connexion
        if 'connexion' in details:
            conn = details['connexion']
            message.append("### 🔌 Stabilité de connexion")
            
            deconnexions = conn.get('deconnexions', 0)
            if deconnexions > 0:
                if deconnexions > 10:
                    message.append(f"⚠️ **Déconnexions**: {deconnexions} (fréquentes)")
                else:
                    message.append(f"ℹ️ **Déconnexions**: {deconnexions} (peu fréquentes)")
            
            echecs = conn.get('echecs', 0)
            if echecs > 0:
                message.append(f"⚠️ **Échecs de connexion**: {echecs}")
            
            temps_moyen = conn.get('temps_moyen_connexion', 'N/A')
            if temps_moyen != 'N/A':
                if isinstance(temps_moyen, (int, float)) and temps_moyen > 500:
                    message.append(f"⚠️ **Temps moyen de connexion**: {temps_moyen} ms (lent)")
                else:
                    message.append(f"ℹ️ **Temps moyen de connexion**: {temps_moyen}")
            
            if 'details' in conn and 'causes_principales' in conn['details']:
                message.append("\n**Causes principales des problèmes de connexion**:")
                for cause in conn['details']['causes_principales']:
                    message.append(f"- {cause}")
            
            message.append("")
        
        # Performance
        if 'performance' in details:
            perf = details['performance']
            message.append("### ⚡ Performance du réseau")
            
            latence = perf.get('latence_moyenne', 'N/A')
            if latence != 'N/A':
                if isinstance(latence, (int, float)) and latence > 100:
                    message.append(f"⚠️ **Latence moyenne**: {latence} ms (élevée)")
                else:
                    message.append(f"✅ **Latence moyenne**: {latence} ms")
            
            debit = perf.get('debit_moyen', 'N/A')
            if debit != 'N/A':
                message.append(f"ℹ️ **Débit moyen**: {debit}")
            
            perte = perf.get('perte_paquets', 'N/A')
            if perte != 'N/A':
                if isinstance(perte, (int, float)) and perte > 1:
                    message.append(f"⚠️ **Perte de paquets**: {perte}% (élevée)")
                else:
                    message.append(f"✅ **Perte de paquets**: {perte}%")
            
            message.append("")
        
        # Interférences
        if 'interferences' in details:
            interf = details['interferences']
            if interf.get('detectees', False):
                message.append("### 📡 Interférences")
                
                impact = interf.get('impact', 0)
                if impact > 7:
                    message.append(f"⚠️ **Impact des interférences**: {impact}/10 (sévère)")
                elif impact > 4:
                    message.append(f"⚠️ **Impact des interférences**: {impact}/10 (modéré)")
                else:
                    message.append(f"ℹ️ **Impact des interférences**: {impact}/10 (faible)")
                
                if 'sources_probables' in interf and interf['sources_probables']:
                    message.append("\n**Sources probables d'interférences**:")
                    for source in interf['sources_probables']:
                        message.append(f"- {source}")
                
                if 'details' in interf and 'canaux_affectes' in interf['details']:
                    message.append(f"\n**Canaux affectés**: {', '.join(str(c) for c in interf['details']['canaux_affectes'])}")
                
                message.append("")
    
    # Points d'accès problématiques
    problematic_aps = analysis.get('problematic_aps', [])
    if isinstance(problematic_aps, list) and problematic_aps:
        message.append("### 📊 Points d'accès problématiques")
        
        ap_count = len(problematic_aps)
        message.append(f"J'ai identifié **{ap_count} points d'accès** avec un SNR faible (inférieur à 25 dB):")
        
        # Limiter à max 3 APs dans l'affichage
        for i, ap in enumerate(problematic_aps[:3]):
            if isinstance(ap, dict) and 'ap_mac' in ap:
                message.append(f"- **{ap['ap_mac']}**: {ap.get('occurrences', 'N/A')} occurrences, SNR moyen: {ap.get('avg_snr', 'N/A')} dB")
        
        if ap_count > 3:
            message.append(f"- Et {ap_count-3} autres points d'accès problématiques")
        
        message.append("\nUn SNR faible peut indiquer un problème de positionnement des points d'accès, d'interférences, ou d'obstacles physiques.")
        message.append("")
    
    return "\n".join(message)
