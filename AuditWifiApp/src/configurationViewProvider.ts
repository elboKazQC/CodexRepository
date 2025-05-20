import * as vscode from 'vscode';

/**
 * Provider pour la vue de configuration Moxa
 */
export class ConfigurationViewProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;
    private _currentConfig: any;

    constructor(private readonly _extensionUri: vscode.Uri) {
        // Configuration par défaut
        this._currentConfig = {
            'min_transmission_rate': 6,
            'max_transmission_power': 20,
            'rts_threshold': 512,
            'fragmentation_threshold': 2346,
            'roaming_mechanism': 'signal_strength',
            'roaming_difference': 9,
            'roaming_threshold_type': 'signal_strength',
            'roaming_threshold_value': -70,
            'ap_candidate_threshold_type': 'signal_strength',
            'ap_candidate_threshold_value': -70,
            'remote_connection_check': true,
            'wmm_enabled': true,
            'turbo_roaming': true,
            'ap_alive_check': true
        };
    }

    /**
     * Renvoie la configuration actuelle
     */
    public getCurrentConfig(): any {
        return this._currentConfig;
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
                case 'updateConfig':
                    this._currentConfig = data.config;
                    break;
                case 'saveConfig':
                    this._saveConfig(data.config);
                    break;
                case 'loadConfig':
                    this._loadConfig();
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
     * Sauvegarde la configuration
     */
    private async _saveConfig(config: any) {
        if (!config) {
            config = this._currentConfig;
        }

        try {
            // Demander à l'utilisateur où sauvegarder le fichier
            const uri = await vscode.window.showSaveDialog({
                filters: {
                    'JSON': ['json']
                },
                saveLabel: 'Sauvegarder la configuration',
                title: 'Sauvegarder la configuration Moxa'
            });

            if (uri) {
                // Ajouter un timestamp à la configuration
                const configToSave = {
                    ...config,
                    timestamp: new Date().toISOString()
                };

                // Écrire le fichier
                await vscode.workspace.fs.writeFile(
                    uri,
                    Buffer.from(JSON.stringify(configToSave, null, 2), 'utf8')
                );

                vscode.window.showInformationMessage('Configuration sauvegardée avec succès!');
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Erreur lors de la sauvegarde: ${error.message}`);
        }
    }

    /**
     * Charge une configuration depuis un fichier
     */
    private async _loadConfig() {
        try {
            // Demander à l'utilisateur de sélectionner un fichier
            const uri = await vscode.window.showOpenDialog({
                canSelectFiles: true,
                canSelectFolders: false,
                canSelectMany: false,
                filters: {
                    'JSON': ['json']
                },
                openLabel: 'Charger la configuration',
                title: 'Charger une configuration Moxa'
            });

            if (uri && uri.length > 0) {
                // Lire le fichier
                const configData = await vscode.workspace.fs.readFile(uri[0]);
                const configStr = Buffer.from(configData).toString('utf8');
                
                // Parser le JSON
                const config = JSON.parse(configStr);
                
                // Mettre à jour la configuration
                this._currentConfig = config;
                
                // Mettre à jour la webview
                this._updateWebview();
                
                vscode.window.showInformationMessage('Configuration chargée avec succès!');
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Erreur lors du chargement: ${error.message}`);
        }
    }

    /**
     * Génère le contenu HTML de la webview
     */
    private _getWebviewContent(): string {
        const config = this._currentConfig;
        
        return `<!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Configuration Moxa</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 10px;
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                }
                .form-group {
                    margin-bottom: 8px;
                }
                label {
                    display: block;
                    margin-bottom: 4px;
                }
                .form-row {
                    display: flex;
                    align-items: center;
                    margin-bottom: 8px;
                }
                .form-row label {
                    margin-right: 10px;
                    min-width: 150px;
                }
                input[type="number"], select {
                    width: 120px;
                    padding: 4px;
                    background-color: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                }
                .checkbox-container {
                    display: flex;
                    align-items: center;
                }
                .checkbox-container input {
                    margin-right: 8px;
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
                hr {
                    border: none;
                    border-top: 1px solid var(--vscode-panel-border);
                    margin: 16px 0;
                }
            </style>
        </head>
        <body>
            <h2>Configuration Moxa</h2>
            
            <div class="section">
                <div class="section-title">Paramètres de transmission</div>
                <div class="form-row">
                    <label for="min_transmission_rate">Taux min (Mbps):</label>
                    <input type="number" id="min_transmission_rate" value="${config.min_transmission_rate}">
                </div>
                <div class="form-row">
                    <label for="max_transmission_power">Puissance max (dBm):</label>
                    <input type="number" id="max_transmission_power" value="${config.max_transmission_power}">
                </div>
                <div class="form-row">
                    <label for="rts_threshold">Seuil RTS:</label>
                    <input type="number" id="rts_threshold" value="${config.rts_threshold}">
                </div>
                <div class="form-row">
                    <label for="fragmentation_threshold">Seuil fragmentation:</label>
                    <input type="number" id="fragmentation_threshold" value="${config.fragmentation_threshold}">
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Paramètres de Roaming</div>
                <div class="form-row">
                    <label for="roaming_mechanism">Mécanisme:</label>
                    <select id="roaming_mechanism">
                        <option value="signal_strength" ${config.roaming_mechanism === 'signal_strength' ? 'selected' : ''}>Signal Strength</option>
                        <option value="snr" ${config.roaming_mechanism === 'snr' ? 'selected' : ''}>SNR</option>
                    </select>
                </div>
                <div class="form-row">
                    <label for="roaming_difference">Différence (dB):</label>
                    <input type="number" id="roaming_difference" value="${config.roaming_difference}">
                </div>
                
                <div class="form-row">
                    <label>Type de seuil:</label>
                    <span class="checkbox-container">
                        <input type="radio" id="roaming_type_snr" name="roaming_threshold_type" value="snr" ${config.roaming_threshold_type === 'snr' ? 'checked' : ''}>
                        <label for="roaming_type_snr">SNR</label>
                    </span>
                    <span class="checkbox-container" style="margin-left: 20px;">
                        <input type="radio" id="roaming_type_signal" name="roaming_threshold_type" value="signal_strength" ${config.roaming_threshold_type === 'signal_strength' ? 'checked' : ''}>
                        <label for="roaming_type_signal">Signal</label>
                    </span>
                </div>
                
                <div class="form-row">
                    <label for="roaming_threshold_value">Seuil de roaming:</label>
                    <input type="number" id="roaming_threshold_value" value="${config.roaming_threshold_value}">
                </div>
                
                <div class="form-row">
                    <label>Type candidat AP:</label>
                    <span class="checkbox-container">
                        <input type="radio" id="ap_type_snr" name="ap_candidate_threshold_type" value="snr" ${config.ap_candidate_threshold_type === 'snr' ? 'checked' : ''}>
                        <label for="ap_type_snr">SNR</label>
                    </span>
                    <span class="checkbox-container" style="margin-left: 20px;">
                        <input type="radio" id="ap_type_signal" name="ap_candidate_threshold_type" value="signal_strength" ${config.ap_candidate_threshold_type === 'signal_strength' ? 'checked' : ''}>
                        <label for="ap_type_signal">Signal</label>
                    </span>
                </div>
                
                <div class="form-row">
                    <label for="ap_candidate_threshold_value">Seuil AP candidat:</label>
                    <input type="number" id="ap_candidate_threshold_value" value="${config.ap_candidate_threshold_value}">
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Options avancées</div>
                <div class="form-row">
                    <span class="checkbox-container">
                        <input type="checkbox" id="turbo_roaming" ${config.turbo_roaming ? 'checked' : ''}>
                        <label for="turbo_roaming">Turbo Roaming</label>
                    </span>
                </div>
                <div class="form-row">
                    <span class="checkbox-container">
                        <input type="checkbox" id="ap_alive_check" ${config.ap_alive_check ? 'checked' : ''}>
                        <label for="ap_alive_check">AP Alive Check</label>
                    </span>
                </div>
                <div class="form-row">
                    <span class="checkbox-container">
                        <input type="checkbox" id="wmm_enabled" ${config.wmm_enabled ? 'checked' : ''}>
                        <label for="wmm_enabled">WMM</label>
                    </span>
                </div>
                <div class="form-row">
                    <span class="checkbox-container">
                        <input type="checkbox" id="remote_connection_check" ${config.remote_connection_check ? 'checked' : ''}>
                        <label for="remote_connection_check">Remote Connection Check</label>
                    </span>
                </div>
            </div>
            
            <div class="buttons">
                <button id="btn-save">Sauvegarder configuration</button>
                <button id="btn-load">Charger configuration</button>
                <button id="btn-analyze">Lancer l'analyse</button>
            </div>

            <script>
                (function() {
                    // Fonction pour récupérer la configuration depuis le formulaire
                    function getFormConfig() {
                        return {
                            min_transmission_rate: parseInt(document.getElementById('min_transmission_rate').value),
                            max_transmission_power: parseInt(document.getElementById('max_transmission_power').value),
                            rts_threshold: parseInt(document.getElementById('rts_threshold').value),
                            fragmentation_threshold: parseInt(document.getElementById('fragmentation_threshold').value),
                            roaming_mechanism: document.getElementById('roaming_mechanism').value,
                            roaming_difference: parseInt(document.getElementById('roaming_difference').value),
                            roaming_threshold_type: document.querySelector('input[name="roaming_threshold_type"]:checked').value,
                            roaming_threshold_value: parseInt(document.getElementById('roaming_threshold_value').value),
                            ap_candidate_threshold_type: document.querySelector('input[name="ap_candidate_threshold_type"]:checked').value,
                            ap_candidate_threshold_value: parseInt(document.getElementById('ap_candidate_threshold_value').value),
                            turbo_roaming: document.getElementById('turbo_roaming').checked,
                            ap_alive_check: document.getElementById('ap_alive_check').checked,
                            wmm_enabled: document.getElementById('wmm_enabled').checked,
                            remote_connection_check: document.getElementById('remote_connection_check').checked
                        };
                    }

                    // Ajouter les écouteurs d'événements
                    document.getElementById('btn-save').addEventListener('click', () => {
                        const config = getFormConfig();
                        const vscode = acquireVsCodeApi();
                        vscode.postMessage({
                            command: 'saveConfig',
                            config: config
                        });
                    });

                    document.getElementById('btn-load').addEventListener('click', () => {
                        const vscode = acquireVsCodeApi();
                        vscode.postMessage({
                            command: 'loadConfig'
                        });
                    });

                    document.getElementById('btn-analyze').addEventListener('click', () => {
                        const config = getFormConfig();
                        // Mettre à jour la configuration actuelle
                        const vscode = acquireVsCodeApi();
                        vscode.postMessage({
                            command: 'updateConfig',
                            config: config
                        });
                        // Lancer l'analyse
                        vscode.postMessage({
                            command: 'analyze'
                        });
                    });

                    // Mettre à jour la configuration en temps réel
                    const inputs = document.querySelectorAll('input, select');
                    inputs.forEach(input => {
                        input.addEventListener('change', () => {
                            const config = getFormConfig();
                            const vscode = acquireVsCodeApi();
                            vscode.postMessage({
                                command: 'updateConfig',
                                config: config
                            });
                        });
                    });
                })();
            </script>
        </body>
        </html>`;
    }
}
