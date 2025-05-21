import * as vscode from 'vscode';
import * as fs from 'fs';
import * as dotenv from 'dotenv';
import MoxaAnalyzer from './moxaAnalyzer';
import { LogsViewProvider } from './logsViewProvider';
import { ConfigurationViewProvider } from './configurationViewProvider';
import { RecommendationsViewProvider } from './recommendationsViewProvider';

// Charger les variables d'environnement
dotenv.config();

// Clé utilisée pour stocker les résultats d'analyse dans l'état de l'extension
const RESULTS_KEY = 'analysisResults';

export function activate(context: vscode.ExtensionContext) {
    console.log('Extension "moxa-wifi-analyzer" is now active');

    // Initialiser l'analyseur Moxa
    const moxaAnalyzer = new MoxaAnalyzer();

    // Créer les fournisseurs de vues pour l'explorateur
    const configViewProvider = new ConfigurationViewProvider(context.extensionUri);
    const logsViewProvider = new LogsViewProvider(context.extensionUri);
    const recommendationsViewProvider = new RecommendationsViewProvider(context.extensionUri);

    // Enregistrer les fournisseurs de vues
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('moxaConfiguration', configViewProvider),
        vscode.window.registerWebviewViewProvider('moxaLogs', logsViewProvider),
        vscode.window.registerWebviewViewProvider('moxaRecommendations', recommendationsViewProvider)
    );

    // Charger d'éventuels résultats précédemment stockés
    const previousResults = context.workspaceState.get(RESULTS_KEY);
    if (previousResults) {
        logsViewProvider.updateResults(previousResults);
        recommendationsViewProvider.updateResults(previousResults);
    }

    // Commande pour analyser les logs
    const analyzeCommand = vscode.commands.registerCommand('moxa-wifi-analyzer.analyze', async () => {
        try {
            // Demander à l'utilisateur de sélectionner un fichier log
            const logFiles = await vscode.window.showOpenDialog({
                canSelectFiles: true,
                canSelectFolders: false,
                canSelectMany: false,
                openLabel: 'Sélectionner un fichier log Moxa',
                filters: {
                    'Logs': ['log', 'txt'],
                    'Tous les fichiers': ['*']
                }
            });

            if (!logFiles || logFiles.length === 0) {
                return;
            }

            const logFilePath = logFiles[0].fsPath;

            // Lire le fichier log
            const logContent = fs.readFileSync(logFilePath, 'utf-8');

            // Obtenir la configuration actuelle
            const config = configViewProvider.getCurrentConfig();

            // Afficher un message de progression
            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Analyse des logs Moxa en cours...",
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0, message: "Préparation de l'analyse..." });

                // Analyser les logs
                try {
                    progress.report({ increment: 30, message: "Traitement des logs..." });
                    
                    const results = await moxaAnalyzer.analyzeLog(logContent, config);
                    await context.workspaceState.update(RESULTS_KEY, results);

                    progress.report({ increment: 70, message: "Génération des recommandations..." });

                    // Mettre à jour les vues avec les résultats stockés
                    const stored = context.workspaceState.get(RESULTS_KEY);
                    logsViewProvider.updateResults(stored);
                    recommendationsViewProvider.updateResults(stored);

                    progress.report({ increment: 100, message: "Analyse terminée!" });

                    // Afficher la vue des recommandations
                    vscode.commands.executeCommand('moxaRecommendations.focus');
                    
                    vscode.window.showInformationMessage(
                        `Analyse terminée avec score: ${results.score}/100. Voir les recommandations pour plus de détails.`
                    );
                } catch (error) {
                    vscode.window.showErrorMessage(`Erreur lors de l'analyse: ${error}`);
                }

                return Promise.resolve();
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Erreur lors de l'analyse: ${error}`);
        }
    });

    // Commande pour afficher les recommandations
    const showRecommendationsCommand = vscode.commands.registerCommand('moxa-wifi-analyzer.showRecommendations', () => {
        const stored = context.workspaceState.get(RESULTS_KEY);
        if (!stored) {
            vscode.window.showInformationMessage('Veuillez d\'abord analyser un fichier log.');
            return;
        }

        logsViewProvider.updateResults(stored);
        recommendationsViewProvider.updateResults(stored);
        vscode.commands.executeCommand('moxaRecommendations.focus');
    });

    // Ajouter les commandes au contexte
    context.subscriptions.push(analyzeCommand, showRecommendationsCommand);
}

export function deactivate() {
    // Nettoyage lors de la désactivation de l'extension
}
