# Script de configuration initiale pour CodeToText sur Windows
# Usage: .\setup.ps1

Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Configuration de CodeToText pour Windows" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Vérifier Python
Write-Host "1️⃣  Vérification de Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "   Téléchargez Python 3.11+ depuis https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Installer uv
Write-Host ""
Write-Host "2️⃣  Installation de uv (gestionnaire de paquets)..." -ForegroundColor Yellow
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    pip install uv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ uv installé avec succès" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Échec de l'installation de uv" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ uv est déjà installé" -ForegroundColor Green
}

# Créer l'environnement virtuel et installer les dépendances
Write-Host ""
Write-Host "3️⃣  Installation des dépendances du projet..." -ForegroundColor Yellow
uv sync
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Dépendances installées avec succès" -ForegroundColor Green
} else {
    Write-Host "   ❌ Échec de l'installation des dépendances" -ForegroundColor Red
    exit 1
}

# Créer le dossier instance/downloads s'il n'existe pas
Write-Host ""
Write-Host "4️⃣  Création des dossiers nécessaires..." -ForegroundColor Yellow
$instancePath = "instance\downloads"
if (-not (Test-Path $instancePath)) {
    New-Item -ItemType Directory -Path $instancePath -Force | Out-Null
    Write-Host "   ✅ Dossier $instancePath créé" -ForegroundColor Green
} else {
    Write-Host "   ✅ Dossier $instancePath existe déjà" -ForegroundColor Green
}

# Résumé
Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ Configuration terminée avec succès!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Prochaines étapes:" -ForegroundColor Yellow
Write-Host "   1. Pour lancer l'application: .\run.ps1" -ForegroundColor White
Write-Host "   2. Ou manuellement: python app.py" -ForegroundColor White
Write-Host "   3. Ouvrez votre navigateur à: http://localhost:5000" -ForegroundColor White
Write-Host ""
