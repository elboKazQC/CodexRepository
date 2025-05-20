# -*- coding: utf-8 -*-
"""
Script de lancement de l'application AuditWifiApp
Ce script permet de lancer l'application et d'afficher les erreurs éventuelles
"""

import sys
import traceback
import subprocess

def check_dependencies():
    """Vérifie et installe les dépendances manquantes si nécessaire"""
    required_packages = [
        'tkinter', 'requests', 'python-dotenv', 'json', 'logging', 
        'datetime', 'threading', 'time', 'subprocess'
    ]
    
    print("Vérification des dépendances...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} est installé")
        except ImportError:
            print(f"⚠️ {package} n'est pas installé. Installation en cours...")
            try:
                # Pour tkinter, c'est un cas spécial car il est généralement inclus avec Python
                if package == 'tkinter':
                    print("tkinter doit être installé avec Python, veuillez vérifier votre installation Python")
                    continue
                
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} a été installé avec succès")
            except Exception as e:
                print(f"❌ Erreur lors de l'installation de {package}: {str(e)}")
                return False
    return True

def main():
    """Fonction principale pour lancer l'application"""
    print("Démarrage de l'application AuditWifiApp...")
    
    try:
        # Vérifier les modules personnalisés
        required_modules = [
            'wifi_data_collector', 'config_manager', 'log_manager', 
            'wifi_test_manager', 'moxa_log_analyzer', 'moxa_roaming_analyzer',
            'wifi_log_analyzer', 'wifi_signal_analyzer', 'wifi_coverage_analyzer'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"✅ Module {module} trouvé")
            except ImportError:
                print(f"❌ Module personnalisé {module} manquant")
                print("Veuillez vérifier que tous les fichiers de l'application sont présents dans le dossier.")
                return
        
        # Importer et exécuter l'application principale
        try:
            # Au lieu d'importer la fonction main, importer le module et exécuter sa fonction main
            import runner_fixed_new
            runner_fixed_new.main()
        except Exception as e:
            print("❌ Erreur lors du lancement de l'application:")
            print(str(e))
            print("\nDétails de l'erreur:")
            traceback.print_exc()
            
    except Exception as e:
        print("❌ Erreur fatale:")
        print(str(e))
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("  AuditWifiApp - Utilitaire d'analyse WiFi et configuration Moxa")
    print("=" * 60)
    
    if check_dependencies():
        main()
    else:
        print("\n❌ Certaines dépendances n'ont pas pu être installées.")
        print("Veuillez les installer manuellement ou contacter le support.")
    
    # Attendre une entrée utilisateur avant de fermer la fenêtre
    input("\nAppuyez sur Entrée pour fermer cette fenêtre...")
