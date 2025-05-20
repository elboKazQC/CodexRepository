import * as fs from 'fs';
import * as path from 'path';
import { MoxaAnalyzerStandalone } from './moxaAnalyzerStandalone';

async function analyzeTestLogs() {
    // Configuration actuelle du Moxa pour le test
    const currentConfig = {
        min_transmission_rate: 6,
        max_transmission_power: 20,
        rts_threshold: 512,
        fragmentation_threshold: 2346,
        roaming_mechanism: 'signal_strength',
        roaming_difference: 9,
        remote_connection_check: true,
        wmm_enabled: true,
        turbo_roaming: true,
        ap_alive_check: true,
        roaming_threshold_type: 'signal_strength',
        roaming_threshold_value: -70,
        ap_candidate_threshold_type: 'signal_strength',
        ap_candidate_threshold_value: -70
    };

    try {
        // Créer l'analyseur
        const analyzer = new MoxaAnalyzerStandalone();

        // Lire le fichier de logs
        const logPath = path.join(__dirname, '..', 'logs_moxa', 'test_roaming_analysis.txt');
        const logContent = fs.readFileSync(logPath, 'utf-8');

        // Analyser les logs
        console.log('Analyse des logs en cours...');
        const results = await analyzer.analyzeLog(logContent, currentConfig);

        // Afficher les résultats
        console.log('\nRésultats de l\'analyse :');
        console.log('Score:', results.score + '/100');
        console.log('\nMétriques de roaming :');
        console.log(JSON.stringify(results.roaming_metrics, null, 2));
        console.log('\nRecommandations :');
        results.recommendations.forEach((rec: string, index: number) => {
            console.log(`${index + 1}. ${rec}`);
        });
        console.log('\nChangements de configuration recommandés :');
        console.log(JSON.stringify(results.config_changes, null, 2));
        console.log('\nAnalyse détaillée :');
        console.log(results.analysis);

        // Sauvegarder les résultats dans un fichier
        const resultsPath = path.join(__dirname, '..', 'logs_moxa', 'analysis_results.json');
        fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
        console.log(`\nRésultats sauvegardés dans ${resultsPath}`);

    } catch (error) {
        console.error('Erreur lors de l\'analyse:', error);
    }
}

// Exécuter l'analyse
analyzeTestLogs();
