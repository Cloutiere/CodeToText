# Script PowerShell pour lancer CodeToText
# Usage: .\run.ps1

Write-Host "🚀 Démarrage de CodeToText..." -ForegroundColor Green

# Vérifier si uv est installé
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv n'est pas installé. Installation en cours..." -ForegroundColor Yellow
    pip install uv
}

# Vérifier si l'environnement virtuel existe
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Création de l'environnement virtuel et installation des dépendances..." -ForegroundColor Cyan
    uv sync
} else {
    Write-Host "✅ Environnement virtuel détecté" -ForegroundColor Green
}

# Activer l'environnement virtuel et lancer l'application
Write-Host "🌐 Lancement de l'application Flask sur http://localhost:5000" -ForegroundColor Cyan
Write-Host "   Appuyez sur Ctrl+C pour arrêter le serveur" -ForegroundColor Gray
Write-Host ""

& .\.venv\Scripts\python.exe app.py
