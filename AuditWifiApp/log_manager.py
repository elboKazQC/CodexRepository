import os
from tkinter import messagebox
from wifi.wifi_analyzer import WifiAnalyzer
from moxa_log_analyzer import MoxaLogAnalyzer
from moxa_roaming_analyzer import MoxaRoamingAnalyzer
from conversational_formatter import format_conversationally

class LogManager:
    """
    Gère les opérations liées aux logs.
    Délègue l'analyse spécifique aux analyseurs spécialisés selon le type de logs à analyser.
    """

    def __init__(self):
        """Instantiate analyzers used for the different log types."""
        self.wifi_analyzer = WifiAnalyzer()
        self.moxa_log_analyzer = MoxaLogAnalyzer()
        self.moxa_roaming_analyzer = MoxaRoamingAnalyzer()

    def analyze_logs(self, log_content, current_config, is_moxa_log=False):
        """
        Analyse les logs et fournit des recommandations, en utilisant l'analyseur approprié.
        
        Args:
            log_content (str): Contenu des logs à analyser
            current_config (dict): Configuration actuelle
            is_moxa_log (bool): Si True, utilise l'analyseur de logs Moxa, sinon utilise l'analyseur WiFi général
            
        Returns:
            dict|str: Résultats de l'analyse
        """
        try:
            # Vérifier si les logs sont vides
            if not log_content or not log_content.strip():
                raise ValueError("Les logs fournis sont vides. Veuillez fournir des logs valides pour l'analyse.")
            
            # Vérifier que la clé API est disponible dans l'environnement
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("La clé API OpenAI n'est pas configurée. Veuillez configurer la variable d'environnement OPENAI_API_KEY.")
            
            # Vérifier que la configuration est correcte
            if not isinstance(current_config, dict):
                raise ValueError("Configuration invalide. La configuration doit être un dictionnaire.")
                
            if is_moxa_log:
                # Détecte si le log concerne spécifiquement des problèmes de roaming
                if "Roaming" in log_content or "roaming" in log_content:
                    # Utiliser l'analyseur spécialisé pour le roaming Moxa
                    try:
                        result = self.moxa_roaming_analyzer.analyze_logs(log_content, current_config)
                        # Vérifier que le résultat est bien un dictionnaire JSON valide
                        if not isinstance(result, dict):
                            raise ValueError("Résultat d'analyse invalide. Format JSON attendu.")
                        # Ajouter le marqueur de type Moxa et la configuration actuelle
                        result["is_moxa_log"] = True
                        result["current_config"] = current_config
                        # Ajouter le format conversationnel
                        result["conversational"] = format_conversationally(result)
                        return result
                    except Exception as e:
                        # Gestion plus détaillée de l'erreur spécifique à l'analyseur
                        raise Exception(f"Erreur lors de l'analyse du roaming Moxa: {str(e)}")
                else:
                    # Utiliser l'analyseur général de logs Moxa
                    try:
                        result = self.moxa_log_analyzer.analyze_logs(log_content, current_config)
                        # Vérifier que le résultat est bien un dictionnaire JSON valide
                        if not isinstance(result, dict):
                            raise ValueError("Résultat d'analyse invalide. Format JSON attendu.")
                        # Ajouter le marqueur de type Moxa et la configuration actuelle
                        result["is_moxa_log"] = True
                        result["current_config"] = current_config
                        # Ajouter le format conversationnel
                        result["conversational"] = format_conversationally(result)
                        return result
                    except Exception as e:
                        # Gestion plus détaillée de l'erreur spécifique à l'analyseur
                        raise Exception(f"Erreur lors de l'analyse des logs Moxa: {str(e)}")
            else:
                # Utiliser l'analyseur Wi-Fi unifié
                try:
                    result = self.wifi_analyzer.analyze_logs(log_content)
                except Exception as e:
                    raise Exception(f"Erreur lors de l'analyse des logs Wi-Fi: {str(e)}")
                
                # Formater les résultats dans une structure similaire pour l'interface utilisateur
                # Générer une version conversationnelle des résultats
                result_dict = {
                    "raw_response": result,
                    "analysis": result,  # Pour maintenir la compatibilité avec l'affichage existant
                    "is_moxa_log": False,  # Indiquer qu'il ne s'agit pas d'un log Moxa
                    "current_config": current_config  # Ajouter la configuration actuelle
                }
                
                # Ajouter le format conversationnel
                result_dict["conversational"] = format_conversationally(result_dict)
                
                return result_dict
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'analyse des logs : {str(e)}")
            # Retourner un résultat minimal en cas d'échec, avec une version conversationnelle
            error_result = {
                "error": str(e),
                "is_moxa_log": is_moxa_log,  # Conserver l'information sur le type de log
                "current_config": current_config,  # Ajouter la configuration actuelle
                "recommendations": ["Impossible d'analyser les logs. Veuillez vérifier votre connexion et votre clé API."],
                "conversational": f"# Erreur lors de l'analyse\n\nJe n'ai pas pu analyser les logs fournis en raison de l'erreur suivante :\n\n```\n{str(e)}\n```\n\n**Recommandation** : Vérifiez votre connexion internet et assurez-vous que votre clé API est correctement configurée. Si le problème persiste, essayez avec un fichier de logs différent ou contactez le support technique."
            }
            return error_result
