# Guide de Configuration - CodeToText sur Windows

## 📋 Prérequis

- Python 3.11 ou supérieur
- uv (gestionnaire de paquets Python moderne)

## 🚀 Installation et Configuration

### 1. Installer uv (si pas déjà installé)

Ouvrez PowerShell et exécutez:

```powershell
# Installation de uv via pip
pip install uv
```

Ou utilisez l'installateur officiel:

```powershell
# Installation via le script officiel
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Installer les dépendances du projet

Dans le répertoire du projet:

```powershell
cd C:\Users\erikc\Documents\ErikAiStudio\CodeToText
uv sync
```

Cette commande va:
- Créer un environnement virtuel automatiquement
- Installer Flask et toutes les dépendances nécessaires

### 3. Lancer l'application

```powershell
# Activer l'environnement virtuel (si nécessaire)
.\.venv\Scripts\Activate.ps1

# Lancer l'application Flask
python app.py
```

L'application sera accessible à: **http://localhost:5000**

## 🎯 Utilisation

1. Ouvrez votre navigateur à `http://localhost:5000`
2. Sélectionnez un profil d'analyse
3. Téléversez un fichier ZIP contenant votre code
4. L'application va traiter le ZIP et générer:
   - Une arborescence du projet
   - Des fichiers consolidés de code
   - Un fichier ZIP téléchargeable avec le code aplati

## 📁 Structure du Projet

```
CodeToText/
├── app.py                    # Application Flask principale
├── analysis_profiles.py      # Définition des profils d'analyse
├── codetotext_core/         # Module core avec utilitaires
│   ├── profiles/            # Classes de base pour les profils
│   ├── utils/               # Fonctions utilitaires
│   └── processing/          # Logique de traitement
├── templates/               # Templates HTML
│   └── index.html
└── instance/                # Dossier d'instance (créé automatiquement)
    └── downloads/           # Fichiers générés
```

## 🔧 Commandes Utiles

### Lancer en mode développement
```powershell
python app.py
```

### Vérifier les dépendances
```powershell
uv pip list
```

### Mettre à jour les dépendances
```powershell
uv sync --upgrade
```

## ⚠️ Dépannage

### Problème: "uv: command not found"
- Assurez-vous que uv est installé: `pip install uv`
- Redémarrez PowerShell après l'installation

### Problème: Erreur d'import de modules
- Vérifiez que l'environnement virtuel est activé
- Réinstallez les dépendances: `uv sync --reinstall`

### Problème: Port 5000 déjà utilisé
- Modifiez le port dans `app.py` (ligne 234): `app.run(host="0.0.0.0", port=5001, debug=True)`

## 📝 Notes

- Le projet était initialement sur Replit, il est maintenant configuré pour Windows
- Les fichiers générés sont stockés dans `instance/downloads/`
- L'application utilise Flask 3.1.0 avec Python 3.11+
