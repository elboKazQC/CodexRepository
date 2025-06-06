# logger.py
# Gestion CSV + sessions

# NOTE: Cette application est destinée à réaliser des audits WiFi dans des usines pour l'implantation d'AMR.
# Le système sera utilisé sur un buggy équipé d'un portable, d'un Moxa et d'un téléphone pour collecter des données.
# Objectifs :
# - Recevoir des alertes visuelles en zones à risque (signal faible, ping élevé, etc.)
# - Permettre la prise de notes sur la localisation ou les incidents
# - Analyser et suggérer des réglages de roaming à partir des logs Moxa
# - Faciliter l'amélioration du roaming WiFi pour l'intégration des AMR
#
# (Pensez à consulter cette note pour garder en tête la finalité du projet et les besoins utilisateurs)

# Ce script est pour PowerShell, ne pas utiliser &&