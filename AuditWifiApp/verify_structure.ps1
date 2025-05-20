$essentialFiles = @(
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

Write-Host "`nVerifying project structure...`n" -ForegroundColor Cyan

Write-Host "Required files:" -ForegroundColor Yellow
foreach ($file in $essentialFiles) {
    if (Test-Path $file) {
        Write-Host "[✓] $file" -ForegroundColor Green
    } else {
        Write-Host "[✗] $file" -ForegroundColor Red
    }
}

Write-Host "`nRequired directories:" -ForegroundColor Yellow
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "[✓] $dir" -ForegroundColor Green
    } else {
        Write-Host "[✗] $dir" -ForegroundColor Red
    }
}
