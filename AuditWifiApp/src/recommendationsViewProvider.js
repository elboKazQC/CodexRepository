"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RecommendationsViewProvider = void 0;
var vscode = require("vscode");
/**
 * Provider pour la vue des recommandations Moxa
 */
var RecommendationsViewProvider = /** @class */ (function () {
    function RecommendationsViewProvider(_extensionUri) {
        this._extensionUri = _extensionUri;
    }
    /**
     * Met à jour les résultats d'analyse
     */
    RecommendationsViewProvider.prototype.updateResults = function (results) {
        this._results = results;
        this._updateWebview();
    };
    /**
     * Appelé quand la vue est créée et affichée pour la première fois
     */
    RecommendationsViewProvider.prototype.resolveWebviewView = function (webviewView, context, _token) {
        var _this = this;
        this._view = webviewView;
        // Configurer la webview
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        // Mettre à jour le contenu initial
        this._updateWebview();
        // Gérer les messages de la webview
        webviewView.webview.onDidReceiveMessage(function (data) {
            switch (data.command) {
                case 'applyConfig':
                    _this._applyRecommendedConfig();
                    break;
            }
        });
    };
    /**
     * Met à jour le contenu de la webview
     */
    RecommendationsViewProvider.prototype._updateWebview = function () {
        if (!this._view) {
            return;
        }
        this._view.webview.html = this._getWebviewContent();
    };
    /**
     * Applique la configuration recommandée
     */
    RecommendationsViewProvider.prototype._applyRecommendedConfig = function () {
        if (!this._results || !this._results.config_changes || this._results.config_changes.length === 0) {
            vscode.window.showInformationMessage('Pas de changements de configuration recommandés.');
            return;
        }
        // Créer un objet de configuration à partir des changements recommandés
        var configChanges = this._results.config_changes;
        var currentConfig = this._results.current_config || {};
        // Créer une copie de la configuration actuelle
        var recommendedConfig = __assign({}, currentConfig);
        // Appliquer les changements recommandés
        for (var _i = 0, configChanges_1 = configChanges; _i < configChanges_1.length; _i++) {
            var change = configChanges_1[_i];
            var param = change.param;
            var recommended = change.recommended;
            if (param && recommended !== undefined) {
                recommendedConfig[param] = recommended;
            }
        }
        // Envoyer la configuration au panneau de configuration
        vscode.commands.executeCommand('moxaConfiguration.applyConfig', recommendedConfig);
        vscode.window.showInformationMessage('Configuration recommandée appliquée! Vérifiez le panneau de configuration.');
    };
    /**
     * Génère le contenu HTML de la webview
     */
    RecommendationsViewProvider.prototype._getWebviewContent = function () {
        var _a, _b, _c, _d;
        var hasResults = !!this._results;
        var recommendationsHtml = '<p>Aucune recommandation disponible.</p>';
        var configChangesHtml = '<p>Aucun changement de configuration suggéré.</p>';
        var insightsHtml = '<p>Pas d\'analyse détaillée disponible.</p>';
        if (hasResults) {
            var results = this._results;
            // Recommandations
            var recommendations = results.recommendations || [];
            if (recommendations.length > 0) {
                recommendationsHtml = '<ul class="recommendations-list">';
                recommendations.forEach(function (rec, index) {
                    recommendationsHtml += "<li class=\"recommendation-item\">".concat(rec, "</li>");
                });
                recommendationsHtml += '</ul>';
            }
            // Changements de configuration
            var configChanges = results.config_changes || [];
            if (configChanges.length > 0) {
                configChangesHtml = '<div class="config-changes">';
                configChanges.forEach(function (change, index) {
                    configChangesHtml += "\n                    <div class=\"config-change-item\">\n                        <div class=\"config-param\">".concat(change.param || 'Paramètre inconnu', "</div>\n                        <div class=\"config-values\">\n                            <div class=\"config-current\">\n                                <span class=\"label\">Actuel:</span> \n                                <span class=\"value\">").concat(change.current !== undefined ? change.current : 'N/A', "</span>\n                            </div>\n                            <div class=\"config-arrow\">\u2192</div>\n                            <div class=\"config-recommended\">\n                                <span class=\"label\">Recommand\u00E9:</span> \n                                <span class=\"value\">").concat(change.recommended !== undefined ? change.recommended : 'N/A', "</span>\n                            </div>\n                        </div>\n                        <div class=\"config-reason\">").concat(change.reason || '', "</div>\n                        ").concat(change.impact ? "<div class=\"config-impact\"><span class=\"label\">Impact:</span> ".concat(change.impact, "</div>") : '', "\n                    </div>");
                });
                configChangesHtml += '</div>';
            }
            // Insights détaillés
            var insights = results.ai_insights || '';
            if (insights) {
                insightsHtml = "<div class=\"insights\">".concat(insights, "</div>");
            }
        }
        return "<!DOCTYPE html>\n        <html lang=\"fr\">\n        <head>\n            <meta charset=\"UTF-8\">\n            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n            <title>Recommandations</title>\n            <style>\n                body {\n                    font-family: var(--vscode-font-family);\n                    padding: 10px;\n                    color: var(--vscode-foreground);\n                    background-color: var(--vscode-editor-background);\n                }\n                .section {\n                    margin-bottom: 16px;\n                    padding: 12px;\n                    border: 1px solid var(--vscode-panel-border);\n                    border-radius: 4px;\n                }\n                .section-title {\n                    font-weight: bold;\n                    margin-bottom: 12px;\n                    color: var(--vscode-sideBarTitle-foreground);\n                }\n                button {\n                    background-color: var(--vscode-button-background);\n                    color: var(--vscode-button-foreground);\n                    border: none;\n                    padding: 6px 12px;\n                    margin-right: 8px;\n                    cursor: pointer;\n                    border-radius: 2px;\n                }\n                button:hover {\n                    background-color: var(--vscode-button-hoverBackground);\n                }\n                .buttons {\n                    margin-top: 16px;\n                }\n                .recommendations-list {\n                    margin: 0;\n                    padding-left: 20px;\n                }\n                .recommendation-item {\n                    margin-bottom: 10px;\n                }\n                .config-changes {\n                    display: flex;\n                    flex-direction: column;\n                    gap: 12px;\n                }\n                .config-change-item {\n                    padding: 8px;\n                    border: 1px solid var(--vscode-panel-border);\n                    border-radius: 4px;\n                    background-color: var(--vscode-editor-background);\n                }\n                .config-param {\n                    font-weight: bold;\n                    margin-bottom: 5px;\n                    color: var(--vscode-editor-foreground);\n                }\n                .config-values {\n                    display: flex;\n                    align-items: center;\n                    margin-bottom: 5px;\n                    flex-wrap: wrap;\n                }\n                .config-current {\n                    margin-right: 10px;\n                }\n                .config-arrow {\n                    margin-right: 10px;\n                    color: var(--vscode-descriptionForeground);\n                }\n                .config-recommended {\n                    color: var(--vscode-terminal-ansiGreen);\n                }\n                .config-reason {\n                    margin-top: 5px;\n                    font-style: italic;\n                    color: var(--vscode-descriptionForeground);\n                }\n                .config-impact {\n                    margin-top: 5px;\n                    color: var(--vscode-editor-foreground);\n                }\n                .label {\n                    font-weight: bold;\n                    margin-right: 5px;\n                }\n                .insights {\n                    white-space: pre-wrap;\n                    line-height: 1.5;\n                }\n                .empty-state {\n                    text-align: center;\n                    margin: 30px 0;\n                    color: var(--vscode-descriptionForeground);\n                }\n                .empty-state-icon {\n                    font-size: 40px;\n                    margin-bottom: 10px;\n                }\n                .collapsible {\n                    cursor: pointer;\n                    padding: 4px 0;\n                }\n                .collapsible-content {\n                    padding: 0 8px;\n                    max-height: 0;\n                    overflow: hidden;\n                    transition: max-height 0.2s ease-out;\n                }\n                .active {\n                    max-height: 500px;\n                }\n            </style>\n        </head>\n        <body>\n            <h2>Recommandations</h2>\n            \n            ".concat(hasResults ? "\n            <div class=\"section\">\n                <div class=\"section-title\">Actions recommand\u00E9es</div>\n                ".concat(recommendationsHtml, "\n            </div>\n            \n            <div class=\"section\">\n                <div class=\"section-title\">Changements de configuration sugg\u00E9r\u00E9s</div>\n                ").concat(configChangesHtml, "\n                ").concat(((_b = (_a = this._results) === null || _a === void 0 ? void 0 : _a.config_changes) === null || _b === void 0 ? void 0 : _b.length) > 0 ? "\n                <div class=\"buttons\">\n                    <button id=\"btn-apply-config\">Appliquer ces changements</button>\n                </div>\n                " : '', "\n            </div>\n            \n            <div class=\"section\">\n                <div class=\"section-title collapsible\" id=\"insights-toggle\">Analyse d\u00E9taill\u00E9e \u25BC</div>\n                <div class=\"collapsible-content\" id=\"insights-content\">\n                    ").concat(insightsHtml, "\n                </div>\n            </div>\n            ") : "\n            <div class=\"empty-state\">\n                <div class=\"empty-state-icon\">\uD83D\uDCA1</div>\n                <p>Pas encore de recommandations disponibles</p>\n                <p>Analysez un fichier log pour obtenir des recommandations personnalis\u00E9es</p>\n            </div>\n            ", "\n\n            <script>\n                (function() {\n                    ").concat(hasResults && ((_d = (_c = this._results) === null || _c === void 0 ? void 0 : _c.config_changes) === null || _d === void 0 ? void 0 : _d.length) > 0 ? "\n                    document.getElementById('btn-apply-config').addEventListener('click', () => {\n                        const vscode = acquireVsCodeApi();\n                        vscode.postMessage({\n                            command: 'applyConfig'\n                        });\n                    });\n                    " : '', "\n                    \n                    // G\u00E9rer la section pliable\n                    const toggle = document.getElementById('insights-toggle');\n                    const content = document.getElementById('insights-content');\n                    \n                    if (toggle && content) {\n                        toggle.addEventListener('click', function() {\n                            this.classList.toggle('active');\n                            if (content.style.maxHeight) {\n                                content.style.maxHeight = null;\n                                toggle.textContent = 'Analyse d\u00E9taill\u00E9e \u25BC';\n                            } else {\n                                content.style.maxHeight = content.scrollHeight + 'px';\n                                toggle.textContent = 'Analyse d\u00E9taill\u00E9e \u25B2';\n                            }\n                        });\n                    }\n                })();\n            </script>\n        </body>\n        </html>");
    };
    return RecommendationsViewProvider;
}());
exports.RecommendationsViewProvider = RecommendationsViewProvider;
