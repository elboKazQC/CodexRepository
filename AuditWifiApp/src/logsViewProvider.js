"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LogsViewProvider = void 0;
var vscode = require("vscode");
/**
 * Provider pour la vue d'analyse des logs Moxa
 */
var LogsViewProvider = /** @class */ (function () {
    function LogsViewProvider(_extensionUri) {
        this._extensionUri = _extensionUri;
    }
    /**
     * Met à jour les résultats d'analyse
     */
    LogsViewProvider.prototype.updateResults = function (results) {
        this._results = results;
        this._updateWebview();
    };
    /**
     * Appelé quand la vue est créée et affichée pour la première fois
     */
    LogsViewProvider.prototype.resolveWebviewView = function (webviewView, context, _token) {
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
                case 'openLog':
                    _this._openLogFile();
                    break;
                case 'saveReport':
                    _this._saveReport();
                    break;
            }
        });
    };
    /**
     * Met à jour le contenu de la webview
     */
    LogsViewProvider.prototype._updateWebview = function () {
        if (!this._view) {
            return;
        }
        this._view.webview.html = this._getWebviewContent();
    };
    /**
     * Ouvre un fichier log pour analyse
     */
    LogsViewProvider.prototype._openLogFile = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                try {
                    // Lancer la commande d'analyse
                    vscode.commands.executeCommand('moxa-wifi-analyzer.analyze');
                }
                catch (error) {
                    vscode.window.showErrorMessage("Erreur lors de l'ouverture du log: ".concat(error.message));
                }
                return [2 /*return*/];
            });
        });
    };
    /**
     * Sauvegarde le rapport d'analyse
     */
    LogsViewProvider.prototype._saveReport = function () {
        return __awaiter(this, void 0, void 0, function () {
            var uri, content, moxaAnalyzer, analyzer, error_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (!this._results) {
                            vscode.window.showInformationMessage('Pas de rapport à sauvegarder. Veuillez d\'abord analyser un log.');
                            return [2 /*return*/];
                        }
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 5, , 6]);
                        return [4 /*yield*/, vscode.window.showSaveDialog({
                                filters: {
                                    'JSON': ['json'],
                                    'Texte': ['txt']
                                },
                                saveLabel: 'Sauvegarder le rapport',
                                title: 'Sauvegarder le rapport d\'analyse'
                            })];
                    case 2:
                        uri = _a.sent();
                        if (!uri) return [3 /*break*/, 4];
                        content = void 0;
                        if (uri.fsPath.toLowerCase().endsWith('.json')) {
                            // Format JSON
                            content = JSON.stringify(this._results, null, 2);
                        }
                        else {
                            moxaAnalyzer = require('./moxaAnalyzer').default;
                            analyzer = new moxaAnalyzer();
                            content = analyzer.getUserFriendlyReport(this._results);
                        }
                        // Écrire le fichier
                        return [4 /*yield*/, vscode.workspace.fs.writeFile(uri, Buffer.from(content, 'utf8'))];
                    case 3:
                        // Écrire le fichier
                        _a.sent();
                        vscode.window.showInformationMessage('Rapport sauvegardé avec succès!');
                        _a.label = 4;
                    case 4: return [3 /*break*/, 6];
                    case 5:
                        error_1 = _a.sent();
                        vscode.window.showErrorMessage("Erreur lors de la sauvegarde: ".concat(error_1.message));
                        return [3 /*break*/, 6];
                    case 6: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Génère le contenu HTML de la webview
     */
    LogsViewProvider.prototype._getWebviewContent = function () {
        var hasResults = !!this._results;
        var metricsHtml = '<p>Aucune donnée disponible.</p>';
        var scoreHtml = '';
        if (hasResults) {
            var results = this._results;
            var metrics = results.roaming_metrics || {};
            var scoreValue = results.score || 0;
            var maxScore = results.max_score || 100;
            var scorePercent = Math.round((scoreValue / maxScore) * 100);
            // Déterminer la couleur du score en fonction de sa valeur
            var scoreColor = 'var(--vscode-charts-red)';
            if (scorePercent >= 80) {
                scoreColor = 'var(--vscode-charts-green)';
            }
            else if (scorePercent >= 60) {
                scoreColor = 'var(--vscode-charts-yellow)';
            }
            else if (scorePercent >= 40) {
                scoreColor = 'var(--vscode-charts-orange)';
            }
            scoreHtml = "\n            <div class=\"score-container\">\n                <div class=\"score\" style=\"color: ".concat(scoreColor, ";\">").concat(scoreValue, "/").concat(maxScore, "</div>\n                <div class=\"score-label\">").concat(results.status || '', "</div>\n            </div>");
            metricsHtml = "\n            <table class=\"metrics-table\">\n                <tr>\n                    <td>\u00C9v\u00E9nements de roaming:</td>\n                    <td>".concat(metrics.total_events || 0, "</td>\n                </tr>\n                <tr>\n                    <td>Temps de basculement moyen:</td>\n                    <td>").concat(metrics.avg_handoff_time || 0, " ms</td>\n                </tr>\n                <tr>\n                    <td>Temps min/max:</td>\n                    <td>").concat(metrics.min_handoff_time || 0, " / ").concat(metrics.max_handoff_time || 0, " ms</td>\n                </tr>\n                <tr>\n                    <td>SNR moyen avant roaming:</td>\n                    <td>").concat(metrics.avg_snr_before || 0, " dB</td>\n                </tr>\n                <tr>\n                    <td>SNR moyen apr\u00E8s roaming:</td>\n                    <td>").concat(metrics.avg_snr_after || 0, " dB</td>\n                </tr>\n                <tr>\n                    <td>Am\u00E9lioration moyenne SNR:</td>\n                    <td>").concat(metrics.snr_improvement || 0, " dB</td>\n                </tr>\n            </table>");
        }
        return "<!DOCTYPE html>\n        <html lang=\"fr\">\n        <head>\n            <meta charset=\"UTF-8\">\n            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n            <title>Analyse des Logs</title>\n            <style>\n                body {\n                    font-family: var(--vscode-font-family);\n                    padding: 10px;\n                    color: var(--vscode-foreground);\n                    background-color: var(--vscode-editor-background);\n                }\n                .section {\n                    margin-bottom: 16px;\n                    padding: 12px;\n                    border: 1px solid var(--vscode-panel-border);\n                    border-radius: 4px;\n                }\n                .section-title {\n                    font-weight: bold;\n                    margin-bottom: 12px;\n                    color: var(--vscode-sideBarTitle-foreground);\n                }\n                button {\n                    background-color: var(--vscode-button-background);\n                    color: var(--vscode-button-foreground);\n                    border: none;\n                    padding: 6px 12px;\n                    margin-right: 8px;\n                    cursor: pointer;\n                    border-radius: 2px;\n                }\n                button:hover {\n                    background-color: var(--vscode-button-hoverBackground);\n                }\n                .buttons {\n                    margin-top: 16px;\n                }\n                .metrics-table {\n                    width: 100%;\n                    border-collapse: collapse;\n                }\n                .metrics-table td {\n                    padding: 4px;\n                    border-bottom: 1px solid var(--vscode-panel-border);\n                }\n                .metrics-table td:first-child {\n                    font-weight: bold;\n                }\n                .score-container {\n                    text-align: center;\n                    margin: 20px 0;\n                }\n                .score {\n                    font-size: 36px;\n                    font-weight: bold;\n                }\n                .score-label {\n                    font-size: 16px;\n                    margin-top: 5px;\n                }\n                .empty-state {\n                    text-align: center;\n                    margin: 30px 0;\n                    color: var(--vscode-descriptionForeground);\n                }\n                .empty-state-icon {\n                    font-size: 40px;\n                    margin-bottom: 10px;\n                }\n            </style>\n        </head>\n        <body>\n            <h2>Analyse des Logs Moxa</h2>\n            \n            ".concat(hasResults ? "\n            ".concat(scoreHtml, "\n            \n            <div class=\"section\">\n                <div class=\"section-title\">M\u00E9triques de Roaming</div>\n                ").concat(metricsHtml, "\n            </div>\n            ") : "\n            <div class=\"empty-state\">\n                <div class=\"empty-state-icon\">\uD83D\uDCCA</div>\n                <p>Pas encore d'analyse disponible</p>\n                <p>Utilisez le bouton ci-dessous pour analyser un fichier log</p>\n            </div>\n            ", "\n            \n            <div class=\"buttons\">\n                <button id=\"btn-open-log\">Ouvrir un log pour analyse</button>\n                ").concat(hasResults ? "<button id=\"btn-save-report\">Sauvegarder le rapport</button>" : '', "\n            </div>\n\n            <script>\n                (function() {\n                    document.getElementById('btn-open-log').addEventListener('click', () => {\n                        const vscode = acquireVsCodeApi();\n                        vscode.postMessage({\n                            command: 'openLog'\n                        });\n                    });\n                    \n                    ").concat(hasResults ? "\n                    document.getElementById('btn-save-report').addEventListener('click', () => {\n                        const vscode = acquireVsCodeApi();\n                        vscode.postMessage({\n                            command: 'saveReport'\n                        });\n                    });\n                    " : '', "\n                })();\n            </script>\n        </body>\n        </html>");
    };
    return LogsViewProvider;
}());
exports.LogsViewProvider = LogsViewProvider;
