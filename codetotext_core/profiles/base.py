# codetotext_core/profiles/base.py
# [Version 2.2]

from __future__ import annotations

import abc
from collections.abc import Iterable
import os


class AnalysisProfile(abc.ABC):
    """
    Classe de base abstraite pour un profil d'analyse de projet.

    Chaque profil encapsule la logique de filtrage des fichiers, de
    catégorisation et de génération de rapports consolidés spécifiques à
    un type de projet.
    """

    # Fichiers de configuration absolument critiques qui ne doivent JAMAIS être ignorés.
    # Ces fichiers sont essentiels pour comprendre et exécuter le projet.
    CRITICAL_CONFIG_BASENAMES: set[str] = {
        "pyproject.toml", # Fichier essentiel pour l'utilisateur (gestion des dépendances/build)
        "requirements.txt", # Dépendances Python
        "dockerfile", "docker-compose.yml", # Docker config
        ".replit", # Replit config
        "replit.md", # Replit documentation
        "package.json", # Frontend package manager
        "vite.config.ts", # Frontend build config
        "tailwind.config.js", # Frontend styling config
        "tsconfig.json", # Frontend TS config
        "tsconfig.node.json", # Frontend TS node config
        "postcss.config.js", # Frontend CSS config
        ".env.example", # Template pour l'environnement
        "README.md", # Documentation principale
        "STRUCTURE.md", # Structure du projet
        "AMELIORATIONS_COMPLETEES.md", # Historique des améliorations
        "CONFIGURATION_COMPLETE.md", # Rapport de configuration
        "DDA_mermaid_1762371637525.md", # Document d'Architecture
        "app.py", # Point d'entrée principal de l'application (par ex: Flask)
        "run.py", # Point d'entrée Flask pour ce projet
        "analysis_profiles.py", # Ce fichier lui-même, utile pour l'auto-analyse
    }

    # EXTENSIONS CRITIQUES A IGNORER SYSTEMATIQUEMENT
    # Inclut les binaires, bases de données, images, polices, archives, etc.
    CRITICAL_IGNORED_EXTENSIONS: set[str] = {
        # Bases de données
        ".rdb", ".db", ".sqlite", ".sqlite3", ".sqlitedb", ".db3",
        # Images & Médias
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp", ".tiff",
        ".mp3", ".mp4", ".wav", ".avi", ".mov",
        # Polices
        ".eot", ".ttf", ".woff", ".woff2", ".otf",
        # Archives & Binaires compilés
        ".zip", ".tar", ".gz", ".rar", ".7z",
        ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".class", ".jar",
        # Documents binaires
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"
    }

    # NOMS DE FICHIERS SPECIFIQUES A IGNORER SYSTEMATIQUEMENT (Lockfiles, etc.)
    CRITICAL_IGNORED_BASENAMES: set[str] = {
        "poetry.lock",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "uv.lock",
        "Gemfile.lock",
        "composer.lock",
        "mix.lock",
        "go.sum",
        "Cargo.lock",
        "dump.rdb", # Explicite au cas où l'extension manque
    }

    @staticmethod
    def is_always_included(path_in_zip: str, path_components: list[str]) -> bool:
        """
        Vérifie si le fichier doit être inclus de manière inconditionnelle,
        indépendamment du profil.

        Règle : Les fichiers d'architecture (DDA_V*.md, MEMO_TECH_V*.md) sont toujours inclus.
        """
        filename = path_components[-1]

        # Check for DDA_V or MEMO_TECH_V prefix (case-insensitive check on the filename)
        if filename.upper().startswith("MEMO_TECH_V") or filename.upper().startswith("DDA_V"):
            return True

        return False

    @staticmethod
    def is_always_ignored(path_in_zip: str, path_components: list[str]) -> bool:
        """
        Vérifie si le fichier doit être ignoré de manière inconditionnelle,
        indépendamment du profil (ex: binaires critiques de base de données, lockfiles).
        """
        filename = path_components[-1]
        _, ext = os.path.splitext(filename)

        # 1. Vérification sur le nom exact (Lockfiles, etc.)
        if filename in AnalysisProfile.CRITICAL_IGNORED_BASENAMES:
            return True

        # 2. Vérification sur l'extension en minuscule
        if ext.lower() in AnalysisProfile.CRITICAL_IGNORED_EXTENSIONS:
            return True

        return False

    @property
    @abc.abstractmethod
    def profile_id(self) -> str:
        """Identifiant unique utilisé dans le formulaire HTML."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def profile_name(self) -> str:
        """Nom lisible par l'humain pour l'affichage."""
        raise NotImplementedError

    @abc.abstractmethod
    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        """
        Détermine si un fichier doit être ignoré en fonction de son chemin.

        Args:
            path_in_zip: Le chemin complet du fichier dans l'archive (ex: "backend/app/models.py").
            path_components: Le chemin décomposé en une liste de répertoires/fichiers
                             (ex: ["backend", "app", "models.py"]).

        Returns:
            True si le fichier doit être ignoré, False sinon.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def categorize_file(self, path_in_zip: str) -> set[str]:
        """
        Attribue une ou plusieurs catégories à un fichier en fonction de son chemin.

        Args:
            path_in_zip: Le chemin complet du fichier dans l'archive.

        Returns:
            Un ensemble de chaînes de caractères représentant les catégories
            (ex: {"BACKEND_CODE", "CONFIG_DOC"}).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:
        """
        Génère le contenu des fichiers consolidés spécifiques à ce profil.

        Args:
            categorized_files: Une liste de tuples, où chaque tuple contient
                               le bloc de contenu d'un fichier et l'ensemble de
                               ses catégories.

        Returns:
            Un dictionnaire où les clés sont les noms des fichiers à générer
            (ex: '__code_taches.txt') et les valeurs sont leur contenu.
        """
        raise NotImplementedError