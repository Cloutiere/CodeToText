# Script pour ouvrir le dossier des fichiers téléchargés
# Usage: .\open_downloads.ps1

$downloadsPath = ".\instance\downloads"

if (Test-Path $downloadsPath) {
    Write-Host "📂 Ouverture du dossier des téléchargements..." -ForegroundColor Green
    explorer.exe (Resolve-Path $downloadsPath)
}
else {
    Write-Host "❌ Le dossier des téléchargements n'existe pas encore." -ForegroundColor Red
    Write-Host "   Il sera créé automatiquement lors du premier téléchargement." -ForegroundColor Yellow
}
