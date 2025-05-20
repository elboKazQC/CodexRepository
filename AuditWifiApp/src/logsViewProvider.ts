import * as vscode from 'vscode';

/**
 * Provider pour la vue d'analyse des logs Moxa
 */
export class LogsViewProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;
    private _results?: any;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    /**
     * Met à jour les résultats d'analyse
     */
    public updateResults(results: any) {
        this._results = results;
        this._updateWebview();
    }

    /**
     * Appelé quand la vue est créée et affichée pour la première fois
     */
    public resolveWebviewView(
        webviewView: vscode.WebviewView, 
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        // Configurer la webview
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        // Mettre à jour le contenu initial
        this._updateWebview();

        // Gérer les messages de la webview
        webviewView.webview.onDidReceiveMessage(data => {
            switch (data.command) {
                case 'openLog':
                    this._openLogFile();
                    break;
                case 'saveReport':
                    this._saveReport();
                    break;
            }
        });
    }

    /**
     * Met à jour le contenu de la webview
     */
    private _updateWebview() {
        if (!this._view) {
            return;
        }

        this._view.webview.html = this._getWebviewContent();
    }

    /**
     * Ouvre un fichier log pour analyse
     */
    private async _openLogFile() {
        try {
            // Lancer la commande d'analyse
            vscode.commands.executeCommand('moxa-wifi-analyzer.analyze');
        } catch (error: any) {
            vscode.window.showErrorMessage(`Erreur lors de l'ouverture du log: ${error.message}`);
        }
    }

    /**
     * Sauvegarde le rapport d'analyse
     */
    private async _saveReport() {
        if (!this._results) {
            vscode.window.showInformationMessage('Pas de rapport à sauvegarder. Veuillez d\'abord analyser un log.');
            return;
        }

        try {
            // Demander à l'utilisateur où sauvegarder le fichier
            const uri = await vscode.window.showSaveDialog({
                filters: {
                    'JSON': ['json'],
                    'Texte': ['txt']
                },
                saveLabel: 'Sauvegarder le rapport',
                title: 'Sauvegarder le rapport d\'analyse'
            });

            if (uri) {
                // Déterminer le format basé sur l'extension
                let content: string;
                if (uri.fsPath.toLowerCase().endsWith('.json')) {
                    // Format JSON
                    content = JSON.stringify(this._results, null, 2);
                } else {
                    // Format texte
                    const moxaAnalyzer = require('./moxaAnalyzer').default;
                    const analyzer = new moxaAnalyzer();
                    content = analyzer.getUserFriendlyReport(this._results);
                }

                // Écrire le fichier
                await vscode.workspace.fs.writeFile(
                    uri,
                    Buffer.from(content, 'utf8')
                );

                vscode.window.showInformationMessage('Rapport sauvegardé avec succès!');
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Erreur lors de la sauvegarde: ${error.message}`);
        }
    }

    /**
     * Génère le contenu HTML de la webview
     */
    private _getWebviewContent(): string {
        const hasResults = !!this._results;
        
        let metricsHtml = '<p>Aucune donnée disponible.</p>';
        let scoreHtml = '';
        
        if (hasResults) {
            const results = this._results;
            const metrics = results.roaming_metrics || {};
            const scoreValue = results.score || 0;
            const maxScore = results.max_score || 100;
            const scorePercent = Math.round((scoreValue / maxScore) * 100);
            
            // Déterminer la couleur du score en fonction de sa valeur
            let scoreColor = 'var(--vscode-charts-red)';
            if (scorePercent >= 80) {
                scoreColor = 'var(--vscode-charts-green)';
            } else if (scorePercent >= 60) {
                scoreColor = 'var(--vscode-charts-yellow)';
            } else if (scorePercent >= 40) {
                scoreColor = 'var(--vscode-charts-orange)';
            }
            
            scoreHtml = `
            <div class="score-container">
                <div class="score" style="color: ${scoreColor};">${scoreValue}/${maxScore}</div>
                <div class="score-label">${results.status || ''}</div>
            </div>`;
            
            metricsHtml = `
            <table class="metrics-table">
                <tr>
                    <td>Événements de roaming:</td>
                    <td>${metrics.total_events || 0}</td>
                </tr>
                <tr>
                    <td>Temps de basculement moyen:</td>
                    <td>${metrics.avg_handoff_time || 0} ms</td>
                </tr>
                <tr>
                    <td>Temps min/max:</td>
                    <td>${metrics.min_handoff_time || 0} / ${metrics.max_handoff_time || 0} ms</td>
                </tr>
                <tr>
                    <td>SNR moyen avant roaming:</td>
                    <td>${metrics.avg_snr_before || 0} dB</td>
                </tr>
                <tr>
                    <td>SNR moyen après roaming:</td>
                    <td>${metrics.avg_snr_after || 0} dB</td>
                </tr>
                <tr>
                    <td>Amélioration moyenne SNR:</td>
                    <td>${metrics.snr_improvement || 0} dB</td>
                </tr>
            </table>`;
        }
        
        return `<!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Analyse des Logs</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 10px;
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                }
                .section {
                    margin-bottom: 16px;
                    padding: 12px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                }
                .section-title {
                    font-weight: bold;
                    margin-bottom: 12px;
                    color: var(--vscode-sideBarTitle-foreground);
                }
                button {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 6px 12px;
                    margin-right: 8px;
                    cursor: pointer;
                    border-radius: 2px;
                }
                button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .buttons {
                    margin-top: 16px;
                }
                .metrics-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .metrics-table td {
                    padding: 4px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .metrics-table td:first-child {
                    font-weight: bold;
                }
                .score-container {
                    text-align: center;
                    margin: 20px 0;
                }
                .score {
                    font-size: 36px;
                    font-weight: bold;
                }
                .score-label {
                    font-size: 16px;
                    margin-top: 5px;
                }
                .empty-state {
                    text-align: center;
                    margin: 30px 0;
                    color: var(--vscode-descriptionForeground);
                }
                .empty-state-icon {
                    font-size: 40px;
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <h2>Analyse des Logs Moxa</h2>
            
            ${hasResults ? `
            ${scoreHtml}
            
            <div class="section">
                <div class="section-title">Métriques de Roaming</div>
                ${metricsHtml}
            </div>
            ` : `
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <p>Pas encore d'analyse disponible</p>
                <p>Utilisez le bouton ci-dessous pour analyser un fichier log</p>
            </div>
            `}
            
            <div class="buttons">
                <button id="btn-open-log">Ouvrir un log pour analyse</button>
                ${hasResults ? `<button id="btn-save-report">Sauvegarder le rapport</button>` : ''}
            </div>

            <script>
                (function() {
                    document.getElementById('btn-open-log').addEventListener('click', () => {
                        const vscode = acquireVsCodeApi();
                        vscode.postMessage({
                            command: 'openLog'
                        });
                    });
                    
                    ${hasResults ? `
                    document.getElementById('btn-save-report').addEventListener('click', () => {
                        const vscode = acquireVsCodeApi();
                        vscode.postMessage({
                            command: 'saveReport'
                        });
                    });
                    ` : ''}
                })();
            </script>
        </body>
        </html>`;
    }
}
