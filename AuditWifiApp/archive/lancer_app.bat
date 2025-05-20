@echo off
echo Lancement de l'application Moxa Analyzer...
python runner_fixed_corrected.py
if %ERRORLEVEL% NEQ 0 (
    echo Une erreur s'est produite lors du lancement de l'application.
    echo Code d'erreur: %ERRORLEVEL%
    pause
) else (
    echo L'application s'est terminée normalement.
)
