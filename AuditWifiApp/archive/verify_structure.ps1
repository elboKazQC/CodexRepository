$requiredFiles = @(
    "api_errors.log",
    "config_manager.py",
    "config.yaml",
    "log_manager.py",
    "logger.py",
    "moxa_analyzer.py",
    "network_scanner.py",
    "runner.py",
    "wifi_analyzer.py",
    "wifi_data_collector.py",
    "wifi_test_manager.py"
)

$requiredDirs = @(
    "src/ai",
    "src/moxa/analyzers",
    "src/moxa/models",
    "src/wifi/analyzers",
    "src/wifi/models",
    "archive",
    "config",
    "logs",
    "logs_moxa"
)

Write-Host "Vérification des fichiers requis..."
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file manquant!" -ForegroundColor Red
    }
}

Write-Host "`nVérification des dossiers requis..."
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✓ $dir" -ForegroundColor Green
    } else {
        Write-Host "✗ $dir manquant!" -ForegroundColor Red
    }
}

Write-Host "`nFichiers non mentionnés dans le README:"
Get-ChildItem -File | Where-Object { $_.Name -notin $requiredFiles -and $_.Name -ne "verify_structure.ps1" -and $_.Name -ne ".gitignore" } | ForEach-Object {
    Write-Host "? $($_.Name)" -ForegroundColor Yellow
}
