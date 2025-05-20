import * as vscode from 'vscode';

/**
 * Provider pour la vue des recommandations Moxa
 */
export class RecommendationsViewProvider implements vscode.WebviewViewProvider {
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
                case 'applyConfig':
                    this._applyRecommendedConfig();
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
     * Applique la configuration recommandée
     */
    private _applyRecommendedConfig() {
        if (!this._results || !this._results.config_changes || this._results.config_changes.length === 0) {
            vscode.window.showInformationMessage('Pas de changements de configuration recommandés.');
            return;
        }

        // Créer un objet de configuration à partir des changements recommandés
        const configChanges = this._results.config_changes;
        const currentConfig = this._results.current_config || {};
        
        // Créer une copie de la configuration actuelle
        const recommendedConfig = { ...currentConfig };
        
        // Appliquer les changements recommandés
        for (const change of configChanges) {
            const param = change.param;
            const recommended = change.recommended;
            if (param && recommended !== undefined) {
                recommendedConfig[param] = recommended;
            }
        }
        
        // Envoyer la configuration au panneau de configuration
        vscode.commands.executeCommand('moxaConfiguration.applyConfig', recommendedConfig);
        
        vscode.window.showInformationMessage('Configuration recommandée appliquée! Vérifiez le panneau de configuration.');
    }

    /**
     * Génère le contenu HTML de la webview
     */
    private _getWebviewContent(): string {
        const hasResults = !!this._results;
        
        let recommendationsHtml = '<p>Aucune recommandation disponible.</p>';
        let configChangesHtml = '<p>Aucun changement de configuration suggéré.</p>';
        let insightsHtml = '<p>Pas d\'analyse détaillée disponible.</p>';
        
        if (hasResults) {
            const results = this._results;
            
            // Recommandations
            const recommendations = results.recommendations || [];
            if (recommendations.length > 0) {
                recommendationsHtml = '<ul class="recommendations-list">';
                recommendations.forEach((rec: string, index: number) => {
                    recommendationsHtml += `<li class="recommendation-item">${rec}</li>`;
                });
                recommendationsHtml += '</ul>';
            }
            
            // Changements de configuration
            const configChanges = results.config_changes || [];
            if (configChanges.length > 0) {
                configChangesHtml = '<div class="config-changes">';
                configChanges.forEach((change: any, index: number) => {
                    configChangesHtml += `
                    <div class="config-change-item">
                        <div class="config-param">${change.param || 'Paramètre inconnu'}</div>
                        <div class="config-values">
                            <div class="config-current">
                                <span class="label">Actuel:</span> 
                                <span class="value">${change.current !== undefined ? change.current : 'N/A'}</span>
                            </div>
                            <div class="config-arrow">→</div>
                            <div class="config-recommended">
                                <span class="label">Recommandé:</span> 
                                <span class="value">${change.recommended !== undefined ? change.recommended : 'N/A'}</span>
                            </div>
                        </div>
                        <div class="config-reason">${change.reason || ''}</div>
                        ${change.impact ? `<div class="config-impact"><span class="label">Impact:</span> ${change.impact}</div>` : ''}
                    </div>`;
                });
                configChangesHtml += '</div>';
            }
            
            // Insights détaillés
            const insights = results.ai_insights || '';
            if (insights) {
                insightsHtml = `<div class="insights">${insights}</div>`;
            }
        }
        
        return `<!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recommandations</title>
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
                .recommendations-list {
                    margin: 0;
                    padding-left: 20px;
                }
                .recommendation-item {
                    margin-bottom: 10px;
                }
                .config-changes {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                .config-change-item {
                    padding: 8px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                    background-color: var(--vscode-editor-background);
                }
                .config-param {
                    font-weight: bold;
                    margin-bottom: 5px;
                    color: var(--vscode-editor-foreground);
                }
                .config-values {
                    display: flex;
                    align-items: center;
                    margin-bottom: 5px;
                    flex-wrap: wrap;
                }
                .config-current {
                    margin-right: 10px;
                }
                .config-arrow {
                    margin-right: 10px;
                    color: var(--vscode-descriptionForeground);
                }
                .config-recommended {
                    color: var(--vscode-terminal-ansiGreen);
                }
                .config-reason {
                    margin-top: 5px;
                    font-style: italic;
                    color: var(--vscode-descriptionForeground);
                }
                .config-impact {
                    margin-top: 5px;
                    color: var(--vscode-editor-foreground);
                }
                .label {
                    font-weight: bold;
                    margin-right: 5px;
                }
                .insights {
                    white-space: pre-wrap;
                    line-height: 1.5;
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
                .collapsible {
                    cursor: pointer;
                    padding: 4px 0;
                }
                .collapsible-content {
                    padding: 0 8px;
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.2s ease-out;
                }
                .active {
                    max-height: 500px;
                }
            </style>
        </head>
        <body>
            <h2>Recommandations</h2>
            
            ${hasResults ? `
            <div class="section">
                <div class="section-title">Actions recommandées</div>
                ${recommendationsHtml}
            </div>
            
            <div class="section">
                <div class="section-title">Changements de configuration suggérés</div>
                ${configChangesHtml}
                ${this._results?.config_changes?.length > 0 ? `
                <div class="buttons">
                    <button id="btn-apply-config">Appliquer ces changements</button>
                </div>
                ` : ''}
            </div>
            
            <div class="section">
                <div class="section-title collapsible" id="insights-toggle">Analyse détaillée ▼</div>
                <div class="collapsible-content" id="insights-content">
                    ${insightsHtml}
                </div>
            </div>
            ` : `
            <div class="empty-state">
                <div class="empty-state-icon">💡</div>
                <p>Pas encore de recommandations disponibles</p>
                <p>Analysez un fichier log pour obtenir des recommandations personnalisées</p>
            </div>
            `}

            <script>
                (function() {
                    ${hasResults && this._results?.config_changes?.length > 0 ? `
                    document.getElementById('btn-apply-config').addEventListener('click', () => {
                        const vscode = acquireVsCodeApi();
                        vscode.postMessage({
                            command: 'applyConfig'
                        });
                    });
                    ` : ''}
                    
                    // Gérer la section pliable
                    const toggle = document.getElementById('insights-toggle');
                    const content = document.getElementById('insights-content');
                    
                    if (toggle && content) {
                        toggle.addEventListener('click', function() {
                            this.classList.toggle('active');
                            if (content.style.maxHeight) {
                                content.style.maxHeight = null;
                                toggle.textContent = 'Analyse détaillée ▼';
                            } else {
                                content.style.maxHeight = content.scrollHeight + 'px';
                                toggle.textContent = 'Analyse détaillée ▲';
                            }
                        });
                    }
                })();
            </script>
        </body>
        </html>`;
    }
}
