# analysis_profiles.py
# [Version 1.4]

from __future__ import annotations

import abc
from collections.abc import Iterable
import os

# ==============================================================================
# 1. CLASSE DE BASE ABSTRAITE (LE CONTRAT)
# ==============================================================================

class AnalysisProfile(abc.ABC):
    """
    Classe de base abstraite pour un profil d'analyse de projet.

    Chaque profil encapsule la logique de filtrage des fichiers, de
    catégorisation et de génération de rapports consolidés spécifiques à
    un type de projet.
    """

    CRITICAL_CONFIG_BASENAMES: set[str] = {
        "pyproject.toml", # Fichier essentiel pour l'utilisateur
        "requirements.txt",
        "dockerfile",
        "docker-compose.yml",
        # Ajout de fichiers critiques spécifiques à cette application
        "app.py", 
        "analysis_profiles.py",
        "replit.md",
    }

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
            path_in_zip: Le chemin complet du fichier dans l'archive.
            path_components: Le chemin décomposé en une liste de répertoires/fichiers.

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
            Un ensemble de chaînes de caractères représentant les catégories.
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

# ==============================================================================
# 2. PROFILS CONCRETS (LES STRATÉGIES)
# ==============================================================================

class AdminScolaireProfile(AnalysisProfile):
    """Profil d'analyse pour le projet 'Administration Scolaire'."""
    profile_id: str = "admin_scolaire"
    profile_name: str = "Projet : Administration Scolaire"

    # --- Règles de filtrage ---
    IGNORED_DIRECTORIES: set[str] = {
        "mon_application/static/assets/sports_budget/", "administration_scolaire_app/static/assets/sports_budget/",
        "tests/", "stubs/",
        "react_apps/sports_budget/src/components/ui/", "react_apps/sports_budget/src/hooks/", "react_apps/sports_budget/src/lib/",
        "attached_assets/", "docs/",
    }
    IGNORED_PATH_COMPONENTS: set[str] = {".git", ".ruff_cache", "__pycache__", "node_modules", ".vscode", "dist", "build", "venv"}
    BOILERPLATE_FILES: set[str] = {
        "migrations/README", "migrations/alembic.ini", "migrations/script.py.mako",
        "administration_scolaire_app/py.typed", "react_apps/sports_budget/index.html", "eslint.config.js",
        "react_apps/sports_budget/tailwind.temp.js", "administration_scolaire_app/taches/routes_backup.py",
        "administration_scolaire_app/taches/routes_merged.py", "administration_scolaire_app/taches/routes_with_duplicate.py",
        "administration_scolaire_app/taches/admin.py",
    }
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "uv.lock", "package-lock.json", "dev.db", "dump.sql", "db_dump.json",
        "budgets_a_importer.json", "import_prod_data_final.sh", "generate_schema.py",
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        filename_lower = path_components[-1].lower()

        # Règle d'inclusion N°1: Ne jamais ignorer les fichiers de configuration critiques (Réponse à la demande utilisateur)
        if filename_lower in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False

        # Le fichier app.py (qui contient la logique de base de Flask) est critique pour cette app, mais pas forcément pour d'autres.
        if path_in_zip in ["app.py", "analysis_profiles.py"]:
            return False

        if any(path_in_zip.startswith(d) for d in self.IGNORED_DIRECTORIES): return True
        if any(comp in self.IGNORED_PATH_COMPONENTS for comp in path_components): return True
        if path_in_zip in self.BOILERPLATE_FILES: return True
        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE: return True
        if filename_lower.endswith((".png", ".ico", ".svg")): return True
        if filename_lower.endswith(".md") and filename_lower != "synthèse_développement.md": return True
        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = set()
        if path_in_zip.startswith("administration_scolaire_app/taches/") or path_in_zip.startswith(
            ("administration_scolaire_app/templates/page_", "administration_scolaire_app/templates/detail_taches.html", "administration_scolaire_app/templates/preparation_horaire.html")
        ) or path_in_zip.startswith(
            ("administration_scolaire_app/static/js/page_", "administration_scolaire_app/static/js/detail_taches.js", "administration_scolaire_app/static/js/preparation_horaire.js")
        ):
            categories.add("TACHES")
        if (path_in_zip.startswith("react_apps/sports_budget/") or path_in_zip.startswith("shared/") or path_in_zip.startswith(
            ("administration_scolaire_app/finance/api_sports.py", "administration_scolaire_app/finance/services_sports_budget.py")
        ) or path_in_zip.startswith(
            ("administration_scolaire_app/templates/sports_budget_loader.html", "administration_scolaire_app/templates/_react_loader_base.html")
        )):
            categories.add("FIN_SPORTIF")
        if (path_in_zip.startswith("administration_scolaire_app/finance/") or path_in_zip.startswith("administration_scolaire_app/journal_entry_service.py")
            or path_in_zip.startswith("administration_scolaire_app/templates/finance/")
            or path_in_zip.startswith(("administration_scolaire_app/static/js/finance", "administration_scolaire_app/static/js/finance_report.js"))
        ):
            categories.add("FIN_GLOBAL")

        return categories if categories else {"COMMUN"}

    def generate_consolidated_files(self, categorized_files: list[tuple[str, set[str]]]) -> dict[str, str]:
        def join_blocks(blocks: Iterable[str]) -> str:
            return "\n\n".join(blocks)

        taches_parts = [b for b, c in categorized_files if "FIN_GLOBAL" not in c and "FIN_SPORTIF" not in c]
        fin_global_parts = [b for b, c in categorized_files if "TACHES" not in c and "FIN_SPORTIF" not in c]
        fin_sportif_parts = [b for b, c in categorized_files if "TACHES" not in c and "FIN_GLOBAL" not in c]
        financier_tot_parts = [b for b, c in categorized_files if "TACHES" not in c]

        return {
            "__code_taches_tot.txt": join_blocks(taches_parts),
            "__code_fin_global.txt": join_blocks(fin_global_parts),
            "__code_fin_sportif.txt": join_blocks(fin_sportif_parts),
            "__code_financier_tot.txt": join_blocks(financier_tot_parts),
        }


class ScenarioBuilderProfile(AnalysisProfile):
    """Profil d'analyse pour le projet 'Scenario Builder'."""
    profile_id: str = "scenario_builder"
    profile_name: str = "Projet : Scenario Builder"

    # --- Règles de filtrage ---
    IGNORED_PATH_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "instance", "attached_assets", "node_modules"
    }
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "poetry.lock", "database.db", "lint.md", "replit.md", ".gitignore"
    }
    MIGRATIONS_BOILERPLATE: set[str] = {
        "README", "alembic.ini", "script.py.mako"
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        filename = path_components[-1]
        filename_lower = filename.lower()

        # Règle d'inclusion N°1: Ne jamais ignorer les fichiers de configuration critiques
        if filename_lower in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False

        if any(comp in self.IGNORED_PATH_COMPONENTS for comp in path_components):
            return True

        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE:
            return True

        # Ignorer les package manager files à la racine, mais pas ceux du frontend
        if filename_lower in ["package.json", "package-lock.json"] and "frontend" not in path_components:
            return True

        # Gérer le cas spécifique du dossier 'migrations' pour ignorer le boilerplate
        # tout en conservant env.py et le contenu de 'versions/'
        if "backend/migrations" in path_in_zip and "versions" not in path_in_zip:
             if filename in self.MIGRATIONS_BOILERPLATE:
                 return True

        if filename_lower.endswith((".png", ".ico", ".svg")):
            return True

        # Ignorer les README.md sauf ceux des dossiers backend et frontend
        if filename_lower == "readme.md":
            if path_in_zip not in ["backend/README.md", "frontend/README.md"]:
                 return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = {"APPLICATION"}

        # --- Segmentation SCENARIO_SOLO_FLOW ---
        SOLO_FLOW_EXACT_PATHS: set[str] = {
            # Backend Routes
            "backend/app/routes/scenario.py",
            "backend/app/routes/story_orchestration.py",
            # Backend Services
            "backend/app/services/ai_service.py",
            # Backend Models
            "backend/app/models/db.py",
            "backend/app/models/enums.py",
            "backend/app/models/dtos.py",
            # Frontend Views/Hooks
            "frontend/src/views/ScenarioHostView/ScenarioHostView.tsx",
            "frontend/src/hooks/useScenario.ts",
        }

        SOLO_FLOW_FRONTEND_PREFIXES: set[str] = {
            "frontend/src/assets/components/CreationModeSelector/",
            "frontend/src/assets/components/WorldIntroductionManager/",
            "frontend/src/assets/components/WorldImageManager/",
        }

        SOLO_FLOW_SCENARIO_CREATION_COMPONENTS: set[str] = {
            "PlotBlueprintViewer",
            "ActGeneratorInterface",
            "Phase1Summary",
            "CharacterImageGenerator",
            "GaleriePersonnages",
            "DossierPersonnage",
        }

        SOLO_FLOW_PROFILE_KEYWORDS: set[str] = {
            "phase1_foundation_guide",
            "phase2_solo_host_assistant",
            "plot_architect",
            "act_generator",
            "clue_assigner_ai",
        }

        is_solo_flow = False

        if path_in_zip in SOLO_FLOW_EXACT_PATHS:
            is_solo_flow = True

        # Frontend Composants de Progression (Par préfixe de dossier)
        elif any(path_in_zip.startswith(prefix) for prefix in SOLO_FLOW_FRONTEND_PREFIXES):
            is_solo_flow = True

        # Frontend Composants de Progression (Par nom dans ScenarioCreation)
        elif path_in_zip.startswith("frontend/src/assets/components/ScenarioCreation/"):
            filename_base = os.path.splitext(os.path.basename(path_in_zip))[0]
            # On vérifie uniquement le nom de base car on veut inclure le .tsx, .ts, et les .module.css associés
            if filename_base in SOLO_FLOW_SCENARIO_CREATION_COMPONENTS:
                is_solo_flow = True

        # Configuration LLM (Progression Solo)
        elif path_in_zip.startswith("backend/seed_data/profiles/"):
            for keyword in SOLO_FLOW_PROFILE_KEYWORDS:
                if keyword in path_in_zip:
                    is_solo_flow = True
                    break

        if is_solo_flow:
            categories.add("SCENARIO_SOLO_FLOW")

        return categories

    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:
        def join_blocks(blocks: Iterable[str]) -> str:
            return "\n\n".join(blocks)

        all_app_parts = [
            block for block, categories in categorized_files if "APPLICATION" in categories
        ]
        solo_flow_parts = [
            block for block, categories in categorized_files if "SCENARIO_SOLO_FLOW" in categories
        ]

        # Conserver le fichier général
        output_files = {"__code_scenario_builder.txt": join_blocks(all_app_parts)}

        # Ajouter le nouveau fichier de segmentation
        if solo_flow_parts:
            output_files["__code_scenario_solo_flow.txt"] = join_blocks(solo_flow_parts)

        return output_files


class CodeToTextProfile(AnalysisProfile):
    """
    Profil d'analyse pour le projet CodeToText lui-même (l'application Flask).
    Utile pour générer un rapport sur sa propre architecture.
    """
    profile_id: str = "codetotext"
    profile_name: str = "Projet : CodeToText (Auto-Analyse)"

    IGNORED_PATH_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "instance", "node_modules", "dist", "build"
    }
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "uv.lock", "generated-icon.png", ".gitignore"
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        filename = path_components[-1]
        filename_lower = filename.lower()

        # Ne jamais ignorer les fichiers critiques définis pour cette application
        # (déjà inclus dans CRITICAL_CONFIG_BASENAMES de la classe mère)
        if filename in ["app.py", "analysis_profiles.py", "replit.md", "pyproject.toml"]:
             return False

        # Ignorer les dossiers/composants spécifiques
        if any(comp in self.IGNORED_PATH_COMPONENTS for comp in path_components):
            # Exception : ne pas ignorer le dossier "templates" même s'il est vide
            if "templates" in path_components and filename.endswith(".html"):
                return False
            return True

        # Fichiers binaires/lock/images non traitables
        if filename_lower.endswith((".png", ".ico", ".svg")):
            return True

        # Fichiers spécifiques à ignorer
        if filename in self.SPECIFIC_FILES_TO_IGNORE:
            return True

        # Ignorer les fichiers internes de Replit si l'utilisateur les a inclus
        if filename in [".replit"]:
            return True # Ils sont gérés génériquement par app.py

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        _, ext = os.path.splitext(path_in_zip)

        if path_in_zip in ["app.py", "analysis_profiles.py"]:
            return {"BACKEND_CORE"}

        if path_in_zip.endswith(".py"):
            return {"BACKEND_UTIL"}

        if path_in_zip.startswith("templates/") and ext == ".html":
            return {"FRONTEND_JINJA"}

        if path_in_zip in ["pyproject.toml", "uv.lock.txt", "replit.md"]:
            return {"CONFIG_DOC"}

        return {"OTHER"}

    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:

        def join_blocks(blocks: Iterable[str]) -> str:
            return "\n\n".join(blocks)

        backend_parts = [b for b, c in categorized_files if "BACKEND_CORE" in c or "BACKEND_UTIL" in c]
        frontend_parts = [b for b, c in categorized_files if "FRONTEND_JINJA" in c]
        config_parts = [b for b, c in categorized_files if "CONFIG_DOC" in c]

        return {
            "__code_codetotext_backend.txt": join_blocks(backend_parts),
            "__code_codetotext_frontend.txt": join_blocks(frontend_parts),
            "__code_codetotext_config.txt": join_blocks(config_parts),
        }

# ==============================================================================
# 3. REGISTRE DES PROFILS DISPONIBLES
# ==============================================================================

PROFILES: dict[str, AnalysisProfile] = {
    p.profile_id: p for p in [
        AdminScolaireProfile(),
        ScenarioBuilderProfile(),
        CodeToTextProfile(),
    ]
}