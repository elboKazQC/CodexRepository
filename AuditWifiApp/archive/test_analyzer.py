# -*- coding: utf-8 -*-
# test_analyzer.py - Test de l'analyseur Moxa amélioré

from moxa_analyzer import MoxaLogAnalyzer

# Créer une instance de l'analyseur
analyzer = MoxaLogAnalyzer()

# Analyser le fichier log test
log_file = 'logs_moxa/test_roaming_log.txt'
results_file = 'logs_moxa/results_test.json'

success = analyzer.analyze_log(log_file, results_file)

if success:
    # Afficher le rapport utilisateur
    report = analyzer.get_user_friendly_report()
    print("\n" + "="*50)
    print("RAPPORT D'ANALYSE MOXA")
    print("="*50)
    print(report)
    print("\n" + "="*50)
    print(f"Les résultats détaillés ont été enregistrés dans {results_file}")
else:
    print("Erreur lors de l'analyse du fichier log.")