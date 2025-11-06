# analysis_profiles.py
# [Version 1.5]

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

# ==============================================================================
# 2. PROFILS CONCRETS (LES STRATÉGIES)
# ==============================================================================

class AdminScolaireProfile(AnalysisProfile):
    """Profil d'analyse pour le projet 'Administration Scolaire'."""
    profile_id: str = "admin_scolaire"
    profile_name: str = "Projet : Administration Scolaire"

    # --- Règles de filtrage ---
    IGNORED_DIRS_OR_COMPONENTS: set[str] = {
        "mon_application/static/assets/sports_budget/", "administration_scolaire_app/static/assets/sports_budget/",
        "tests/", "stubs/",
        "react_apps/sports_budget/src/components/ui/", "react_apps/sports_budget/src/hooks/", "react_apps/sports_budget/src/lib/",
        "attached_assets/", "docs/",
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "node_modules", "dist", "build", "instance"
    }
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "uv.lock", "dev.db", "dump.sql", "db_dump.json",
        "budgets_a_importer.json", "import_prod_data_final.sh", "generate_schema.py",
        "package-lock.json" # Ignorer package-lock.json
    }
    BOILERPLATE_FILES: set[str] = {
        "migrations/README", "migrations/alembic.ini", "migrations/script.py.mako",
        "administration_scolaire_app/py.typed", "react_apps/sports_budget/index.html", "eslint.config.js",
        "react_apps/sports_budget/tailwind.temp.js", "administration_scolaire_app/taches/routes_backup.py",
        "administration_scolaire_app/taches/routes_merged.py", "administration_scolaire_app/taches/routes_with_duplicate.py",
        "administration_scolaire_app/taches/admin.py",
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        filename_lower = path_components[-1].lower()

        # Règle d'inclusion N°1: Ne jamais ignorer les fichiers de configuration critiques
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False
        if filename_lower == "readme.md" and path_in_zip == "readme.md": # Le README racine est critique
            return False

        # Ignorer les fichiers binaires et lock
        if filename_lower.endswith((".png", ".ico", ".svg")): return True
        if filename_lower.endswith(".lock"): return True
        if filename_lower.endswith(".db"): return True
        if filename_lower.endswith(".sql"): return True
        if filename_lower.endswith(".json") and filename_lower != "package.json": # Autoriser package.json
            return True
        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE: return True

        # Ignorer les dossiers spécifiques
        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            # Exception: Ne pas ignorer les fichiers de migration, même si 'versions' est dans IGNORED_DIRS_OR_COMPONENTS
            if path_in_zip.startswith("administration_scolaire_app/migrations/versions/"):
                 return False
            return True

        # Ignorer les .md non critiques et certains fichiers de boilerplate
        if filename_lower.endswith(".md") and filename_lower != "readme.md": return True
        if path_in_zip in self.BOILERPLATE_FILES: return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = set()
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            categories.add("CONFIG_DOC")

        # --- Segmentation par domaine ---
        if path_in_zip.startswith("administration_scolaire_app/"):
            if path_in_zip.endswith(".py"):
                if "taches" in path_in_zip:
                    categories.add("TACHES")
                elif "finance" in path_in_zip or "journal_entry_service.py" in path_in_zip:
                    categories.add("FIN_GLOBAL")
                elif "api_sports.py" in path_in_zip or "services_sports_budget.py" in path_in_zip:
                    categories.add("FIN_SPORTIF")
                elif "app.py" in path_in_zip: # Le run.py de flask doit être bien identifié
                    categories.add("BACKEND_CORE")
                elif "config.py" in path_in_zip:
                    categories.add("BACKEND_CONFIG")
                elif path_in_zip.startswith("administration_scolaire_app/templates/"):
                    if "finance/finance_report.html" in path_in_zip or "finance" in path_in_zip:
                        categories.add("FIN_GLOBAL")
                    if "sports_budget_loader.html" in path_in_zip or "react_loader_base.html" in path_in_zip:
                        categories.add("FIN_SPORTIF")
                elif path_in_zip.startswith("administration_scolaire_app/static/js/"):
                    if "finance_report.js" in path_in_zip or "finance" in path_in_zip:
                        categories.add("FIN_GLOBAL")
                    if "sports_budget" in path_in_zip:
                        categories.add("FIN_SPORTIF")

        elif path_in_zip.startswith("react_apps/sports_budget/"):
            categories.add("FIN_SPORTIF")

        elif path_in_zip.startswith("shared/"):
            categories.add("FIN_SPORTIF") # Shared est utilisé par le module sportif

        elif path_in_zip.endswith(".md"):
            categories.add("CONFIG_DOC")

        elif path_in_zip.endswith(".ini"):
            categories.add("BACKEND_CONFIG")

        elif path_in_zip.endswith(".json"): # Package.json is critical config
            if path_in_zip == "package.json":
                categories.add("FRONTEND_CONFIG")
            # Other JSON files are ignored anyway.

        elif path_in_zip.startswith("frontend/"):
            if path_in_zip.endswith((".tsx", ".ts", ".jsx", ".js")):
                if "frontend/src/" in path_in_zip and not path_in_zip.endswith("vite-env.d.ts"):
                    categories.add("FRONTEND_CODE")
                else: # vite.config.ts, tsconfig.json, etc.
                    categories.add("FRONTEND_CONFIG")
            elif path_in_zip.endswith(".css"):
                categories.add("FRONTEND_STATIC")
            elif path_in_zip.endswith(".html"):
                categories.add("FRONTEND_STATIC")

        # Si aucune catégorie n'a été attribuée, assigner 'OTHER'
        if not categories:
            categories.add("OTHER")

        return categories

    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:
        def join_blocks(blocks: Iterable[str]) -> str:
            return "\n\n".join(blocks)

        taches_parts = [b for b, c in categorized_files if "TACHES" in c]
        fin_global_parts = [b for b, c in categorized_files if "FIN_GLOBAL" in c]
        fin_sportif_parts = [b for b, c in categorized_files if "FIN_SPORTIF" in c]

        # Regroupement des fichiers de configuration et documentation
        config_doc_parts = [b for b, c in categorized_files if "CONFIG_DOC" in c]
        backend_core_parts = [b for b, c in categorized_files if "BACKEND_CORE" in c]
        backend_config_parts = [b for b, c in categorized_files if "BACKEND_CONFIG" in c]
        backend_util_parts = [b for b, c in categorized_files if "BACKEND_UTIL" in c]
        frontend_code_parts = [b for b, c in categorized_files if "FRONTEND_CODE" in c]
        frontend_static_parts = [b for b, c in categorized_files if "FRONTEND_STATIC" in c]
        frontend_config_parts = [b for b, c in categorized_files if "FRONTEND_CONFIG" in c]
        tests_parts = [b for b, c in categorized_files if "TESTS" in c]
        other_parts = [b for b, c in categorized_files if "OTHER" in c]

        output_files: dict[str, str] = {}

        # Consolidation des fichiers critiques et de configuration
        output_files["__code_admin_scolaire_taches.txt"] = join_blocks(taches_parts)
        output_files["__code_admin_scolaire_fin_global.txt"] = join_blocks(fin_global_parts)
        output_files["__code_admin_scolaire_fin_sportif.txt"] = join_blocks(fin_sportif_parts)

        # Consolider les fichiers de config, core, util et frontend en un seul bloc pour une vue globale
        output_files["__code_admin_scolaire_config_docs.txt"] = join_blocks(
            config_doc_parts + backend_core_parts + backend_config_parts +
            backend_util_parts + frontend_code_parts + frontend_static_parts +
            frontend_config_parts
        )

        if tests_parts:
            output_files["__code_admin_scolaire_tests.txt"] = join_blocks(tests_parts)
        if other_parts:
            output_files["__code_admin_scolaire_other.txt"] = join_blocks(other_parts)

        return output_files

class ScenarioBuilderProfile(AnalysisProfile):
    """Profil d'analyse pour le projet 'Scenario Builder'."""
    profile_id: str = "scenario_builder"
    profile_name: str = "Projet : Scenario Builder"

    # --- Règles de filtrage ---
    IGNORED_DIRS_OR_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "instance", "attached_assets", "node_modules", "dist", "build", "tests"
    }
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "poetry.lock", "database.db", "lint.md", "replit.md", ".gitignore", # replit.md is critical for mermaid, so it should not be ignored for MermaidProfile.
        "package-lock.json"
    }
    MIGRATIONS_BOILERPLATE: set[str] = {
        "README", "alembic.ini", "script.py.mako"
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        filename = path_components[-1]
        filename_lower = filename.lower()

        # Règle d'inclusion N°1: Ne jamais ignorer les fichiers de configuration critiques
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False
        if filename_lower == "readme.md" and path_in_zip == "readme.md": # Le README racine est critique
            return False

        # Ignorer les fichiers binaires et lock
        if filename_lower.endswith((".png", ".ico", ".svg")): return True
        if filename_lower.endswith(".lock"): return True
        if filename_lower.endswith(".db"): return True
        if filename_lower.endswith(".sql"): return True
        if filename_lower.endswith(".json") and filename_lower != "package.json": # Autoriser package.json
            return True
        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE: return True

        # Ignorer les dossiers spécifiques
        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            # Exception: Ne pas ignorer les fichiers de migration, même si 'versions' est dans IGNORED_DIRS_OR_COMPONENTS
            if path_in_zip.startswith("scenario_builder_app/migrations/versions/"):
                 return False
            return True

        # Ignorer les .md non critiques et certains fichiers de boilerplate
        if filename_lower.endswith(".md") and filename_lower != "readme.md": return True
        if path_in_zip in self.MIGRATIONS_BOILERPLATE: return True # Specific boilerplate for migrations

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = set()
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            categories.add("CONFIG_DOC")

        # --- Segmentation SCENARIO_SOLO_FLOW ---
        SOLO_FLOW_EXACT_PATHS: set[str] = {
            "scenario_builder_app/routes/scenario.py",
            "scenario_builder_app/routes/story_orchestration.py",
            "scenario_builder_app/services/ai_service.py",
            "scenario_builder_app/models/db.py",
            "scenario_builder_app/models/enums.py",
            "scenario_builder_app/models/dtos.py",
            "react_apps/sports_budget/src/views/ScenarioHostView/ScenarioHostView.tsx",
            "react_apps/sports_budget/src/hooks/useScenario.ts",
        }
        SOLO_FLOW_FRONTEND_PREFIXES: set[str] = {
            "react_apps/sports_budget/src/assets/components/CreationModeSelector/",
            "react_apps/sports_budget/src/assets/components/WorldIntroductionManager/",
            "react_apps/sports_budget/src/assets/components/WorldImageManager/",
        }
        SOLO_FLOW_SCENARIO_CREATION_COMPONENTS: set[str] = {
            "PlotBlueprintViewer", "ActGeneratorInterface", "Phase1Summary",
            "CharacterImageGenerator", "GaleriePersonnages", "DossierPersonnage",
        }
        SOLO_FLOW_PROFILE_KEYWORDS: set[str] = {
            "phase1_foundation_guide", "phase2_solo_host_assistant",
            "plot_architect", "act_generator", "clue_assigner_ai",
        }

        is_solo_flow = False
        if path_in_zip in SOLO_FLOW_EXACT_PATHS: is_solo_flow = True
        elif any(path_in_zip.startswith(prefix) for prefix in SOLO_FLOW_FRONTEND_PREFIXES): is_solo_flow = True
        elif path_in_zip.startswith("react_apps/sports_budget/src/assets/components/ScenarioCreation/"):
            filename_base = os.path.splitext(os.path.basename(path_in_zip))[0]
            if filename_base in SOLO_FLOW_SCENARIO_CREATION_COMPONENTS: is_solo_flow = True
        elif path_in_zip.startswith("backend/seed_data/profiles/"):
            for keyword in SOLO_FLOW_PROFILE_KEYWORDS:
                if keyword in path_in_zip:
                    is_solo_flow = True
                    break

        if is_solo_flow: categories.add("SCENARIO_SOLO_FLOW")

        # --- Segmentation par domaine ---
        if path_in_zip.startswith("scenario_builder_app/"):
            if path_in_zip.endswith(".py"):
                if "routes" in path_in_zip or "services" in path_in_zip:
                    categories.add("BACKEND_CODE")
                elif "models" in path_in_zip or "enums.py" in path_in_zip or "dtos.py" in path_in_zip:
                    categories.add("BACKEND_CORE")
                elif "config.py" in path_in_zip:
                    categories.add("BACKEND_CONFIG")
                elif path_in_zip.startswith("scenario_builder_app/migrations/"):
                    categories.add("BACKEND_MIGRATIONS")
                elif path_in_zip.startswith("scenario_builder_app/tests/"):
                    categories.add("TESTS")
                else:
                    categories.add("BACKEND_UTIL")
            elif path_in_zip.startswith("scenario_builder_app/migrations/") and os.path.splitext(path_in_zip)[1].lower() == ".ini":
                categories.add("BACKEND_CONFIG")
        elif path_in_zip.startswith("react_apps/"):
            if path_in_zip.endswith((".tsx", ".ts", ".jsx", ".js")):
                if "src/" in path_in_zip: categories.add("FRONTEND_CODE")
                else: categories.add("FRONTEND_CONFIG")
            elif path_in_zip.endswith(".css"):
                categories.add("FRONTEND_STATIC")
            elif path_in_zip.endswith(".html"):
                categories.add("FRONTEND_STATIC")
        elif path_in_zip.startswith("shared/"):
            categories.add("FIN_SPORTIF") # Shared est utilisé par le module sportif

        elif path_in_zip.endswith(".md"):
            categories.add("CONFIG_DOC")
        elif path_in_zip == "package.json":
            categories.add("FRONTEND_CONFIG")
        elif path_in_zip == "replit.md":
            categories.add("CONFIG_DOC")

        # Si aucune catégorie n'a été attribuée, assigner 'OTHER'
        if not categories:
            categories.add("OTHER")

        return categories

    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:
        def join_blocks(blocks: Iterable[str]) -> str:
            return "\n\n".join(blocks)

        solo_flow_parts = [b for b, c in categorized_files if "SCENARIO_SOLO_FLOW" in c]
        taches_parts = [b for b, c in categorized_files if "TACHES" in c]
        fin_global_parts = [b for b, c in categorized_files if "FIN_GLOBAL" in c]
        fin_sportif_parts = [b for b, c in categorized_files if "FIN_SPORTIF" in c]

        config_doc_parts = [b for b, c in categorized_files if "CONFIG_DOC" in c]
        backend_core_parts = [b for b, c in categorized_files if "BACKEND_CORE" in c]
        backend_config_parts = [b for b, c in categorized_files if "BACKEND_CONFIG" in c]
        backend_migrations_parts = [b for b, c in categorized_files if "BACKEND_MIGRATIONS" in c]
        backend_util_parts = [b for b, c in categorized_files if "BACKEND_UTIL" in c]
        frontend_code_parts = [b for b, c in categorized_files if "FRONTEND_CODE" in c]
        frontend_static_parts = [b for b, c in categorized_files if "FRONTEND_STATIC" in c]
        frontend_config_parts = [b for b, c in categorized_files if "FRONTEND_CONFIG" in c]
        tests_parts = [b for b, c in categorized_files if "TESTS" in c]
        other_parts = [b for b, c in categorized_files if "OTHER" in c]

        output_files: dict[str, str] = {}

        output_files["__code_scenario_builder_solo_flow.txt"] = join_blocks(solo_flow_parts)
        output_files["__code_scenario_builder_taches.txt"] = join_blocks(taches_parts)
        output_files["__code_scenario_builder_fin_global.txt"] = join_blocks(fin_global_parts)
        output_files["__code_scenario_builder_fin_sportif.txt"] = join_blocks(fin_sportif_parts)

        # Consolider les fichiers critiques et de configuration
        output_files["__code_scenario_builder_config_docs.txt"] = join_blocks(
            config_doc_parts + backend_core_parts + backend_config_parts +
            backend_util_parts + frontend_code_parts + frontend_static_parts +
            frontend_config_parts
        )

        if tests_parts:
            output_files["__code_scenario_builder_tests.txt"] = join_blocks(tests_parts)
        if other_parts:
            output_files["__code_scenario_builder_other.txt"] = join_blocks(other_parts)

        return output_files

# --- NOUVEAU PROFIL POUR MERMAID ---
class MermaidProfile(AnalysisProfile):
    """Profil d'analyse pour le projet Mermaid Editor."""
    profile_id: str = "mermaid"
    profile_name: str = "Projet : Mermaid Editor"

    # --- Règles d'ignorance ---
    # Dossiers ou composants à ignorer complètement
    IGNORED_DIRS_OR_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "node_modules", "dist", "build", "tests", "instance", "attached_assets",
        "migrations/versions" # Ignore the actual generated migration files content for this profile
    }
    # Fichiers spécifiques à ignorer, indépendamment de leur dossier
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "package-lock.json", # Large, not code
        "uv.lock",
        ".gitignore",
        "*.png", "*.ico", "*.svg", # Binary image files
        "*.db", "*.sql", "*.lock", # Generic database/lock files
        "*.log", # Generic log files
        "*.json", # Generic JSON files unless they are critical config like package.json
    }
    # Fichiers de configuration critiques qui NE doivent JAMAIS être ignorés.
    CRITICAL_CONFIG_FILES: set[str] = {
        # Root level critical configs and docs
        ".env.example", # Keep this as a critical config template
        "AMELIORATIONS_COMPLETEES.md", "CONFIGURATION_COMPLETE.md", "DDA_mermaid_1762371637525.md",
        "README.md", "STRUCTURE.md", "replit.md", ".replit",
        # Backend critical configs/entry points
        "backend/run.py",
        "backend/app/__init__.py", "backend/app/config.py", "backend/app/models.py",
        "backend/app/schemas.py", "backend/requirements.txt",
        "backend/migrations/alembic.ini",
        "backend/app/routes/mermaid.py", # Specific critical route for this project
        "backend/app/services/mermaid_parser.py", "backend/app/services/mermaid_generator.py", # Specific critical services
        "backend/app/routes/nodes.py", # As it contains Node/Relationship logic used by Mermaid
        "backend/app/routes/subprojects.py", # As it contains SubProject logic used by Mermaid
        "backend/app/services/nodes.py",
        "backend/app/services/subprojects.py",
        # Frontend critical configs/entry points
        "frontend/package.json",
        "frontend/vite.config.ts",
        "frontend/tailwind.config.js",
        "frontend/tsconfig.json",
        "frontend/tsconfig.node.json",
        "frontend/postcss.config.js",
        "frontend/src/types/api.ts", # Frontend types are critical for communication
        "frontend/src/App.tsx", "frontend/src/main.tsx", # Main frontend components
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        filename = path_components[-1]
        filename_lower = filename.lower()

        # 1. Never ignore critical config/doc files.
        if path_in_zip in self.CRITICAL_CONFIG_FILES:
            return False
        # .env.example is critical as it shows what's needed.

        # 2. Ignore specific large/non-code files and general patterns.
        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE:
            return True
        # Ensure general JSON files are ignored unless they are critical config (like package.json)
        if filename_lower.endswith(".json") and path_in_zip != "frontend/package.json":
            return True

        # 3. Ignore common development/build/cache directories.
        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            # Exception: Allow files inside migrations/versions/ as they might contain code history
            if path_in_zip.startswith("backend/migrations/versions/"):
                return False
            return True # If any component matches an ignored dir, ignore the file.

        # 4. Ignore specific MD files that are not critical docs.
        if filename_lower.endswith(".md") and path_in_zip not in ["README.md", "STRUCTURE.md", "AMELIORATIONS_COMPLETEES.md", "CONFIGURATION_COMPLETE.md", "DDA_mermaid_1762371637525.md", "replit.md"]:
            return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = set()

        # --- Add Critical Configs first ---
        if path_in_zip in self.CRITICAL_CONFIG_FILES:
            categories.add("CONFIG_DOC")

        # --- Backend Categories ---
        if path_in_zip.startswith("backend/"):
            if path_in_zip.endswith(".py"):
                if "routes" in path_in_zip:
                    if "mermaid.py" in path_in_zip: categories.add("BACKEND_CODE_CRITICAL")
                    elif "nodes.py" in path_in_zip or "subprojects.py" in path_in_zip:
                         categories.add("BACKEND_CODE_CRITICAL") # Also critical for Mermaid logic
                    else: categories.add("BACKEND_CODE")
                elif "services" in path_in_zip:
                    if "mermaid_parser.py" in path_in_zip or "mermaid_generator.py" in path_in_zip:
                        categories.add("BACKEND_SERVICES_CRITICAL")
                    elif "nodes.py" in path_in_zip or "subprojects.py" in path_in_zip:
                        categories.add("BACKEND_CODE_CRITICAL") # These are also critical for Mermaid structure
                    else:
                        categories.add("BACKEND_CODE")
                elif "models.py" in path_in_zip or "schemas.py" in path_in_zip:
                    categories.add("BACKEND_CORE")
                elif "run.py" in path_in_zip or "__init__.py" in path_in_zip or "config.py" in path_in_zip:
                    categories.add("BACKEND_CORE")
                elif path_in_zip.startswith("backend/migrations/"): # Specific handling for migration scripts
                    categories.add("BACKEND_MIGRATIONS")
                elif path_in_zip.startswith("backend/tests/"):
                    categories.add("TESTS")
                else: # Catch all other backend python files
                    categories.add("BACKEND_UTIL") 
            elif path_in_zip == "backend/requirements.txt":
                 categories.add("BACKEND_CONFIG")
            elif path_in_zip.startswith("backend/migrations/") and os.path.splitext(path_in_zip)[1].lower() == ".ini":
                 categories.add("BACKEND_CONFIG")
            elif path_in_zip == "backend/.replit":
                 categories.add("CONFIG_DOC") # Treat .replit as config/doc

        # --- Frontend Categories ---
        elif path_in_zip.startswith("frontend/"):
            if path_in_zip.endswith((".tsx", ".ts", ".jsx", ".js")):
                if "frontend/src/" in path_in_zip:
                    if "frontend/src/types/api.ts" in path_in_zip: categories.add("FRONTEND_TYPES")
                    elif "frontend/src/App.tsx" in path_in_zip or "frontend/src/main.tsx" in path_in_zip: categories.add("FRONTEND_CODE")
                    else: categories.add("FRONTEND_CODE")
                else: # vite.config.ts, tsconfig.json, vite-env.d.ts etc. are config
                    categories.add("FRONTEND_CONFIG")
            elif path_in_zip.endswith(".css"):
                categories.add("FRONTEND_STATIC")
            elif path_in_zip.endswith(".html"):
                categories.add("FRONTEND_STATIC")
            elif path_in_zip == "frontend/package.json":
                categories.add("FRONTEND_CONFIG")
            elif path_in_zip in ["frontend/vite.config.ts", "frontend/tailwind.config.js", "frontend/tsconfig.json", "frontend/tsconfig.node.json", "frontend/postcss.config.js"]:
                categories.add("FRONTEND_CONFIG")

        # --- Catch All ---
        if not categories:
            categories.add("OTHER")

        return categories

    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:
        def join_blocks(blocks: Iterable[str]) -> str:
            return "\n\n".join(blocks)

        backend_core_parts = [b for b, c in categorized_files if "BACKEND_CORE" in c]
        backend_config_parts = [b for b, c in categorized_files if "BACKEND_CONFIG" in c]
        backend_routes_critical_parts = [b for b, c in categorized_files if "BACKEND_ROUTES_CRITICAL" in c]
        backend_services_critical_parts = [b for b, c in categorized_files if "BACKEND_SERVICES_CRITICAL" in c]
        backend_code_parts = [b for b, c in categorized_files if "BACKEND_CODE" in c and not ("BACKEND_CORE" in c or "BACKEND_CONFIG" in c or "BACKEND_MIGRATIONS" in c or "BACKEND_ROUTES_CRITICAL" in c or "BACKEND_SERVICES_CRITICAL" in c)]
        backend_migrations_parts = [b for b, c in categorized_files if "BACKEND_MIGRATIONS" in c]

        frontend_code_parts = [b for b, c in categorized_files if "FRONTEND_CODE" in c]
        frontend_static_parts = [b for b, c in categorized_files if "FRONTEND_STATIC" in c]
        frontend_config_parts = [b for b, c in categorized_files if "FRONTEND_CONFIG" in c]
        frontend_types_parts = [b for b, c in categorized_files if "FRONTEND_TYPES" in c]

        config_doc_parts = [b for b, c in categorized_files if "CONFIG_DOC" in c]
        tests_parts = [b for b, c in categorized_files if "TESTS" in c]
        other_parts = [b for b, c in categorized_files if "OTHER" in c]

        output_files = {}

        # Backend Consolidation: Combine core, config, critical routes/services, and general code
        # Ensure critical pieces are clearly identifiable.
        output_files["__code_mermaid_backend.txt"] = join_blocks(
            backend_core_parts + 
            [b for b in backend_config_parts if "requirements.txt" in b or ".replit" in b] + # Include only key config files here
            backend_routes_critical_parts + 
            backend_services_critical_parts + 
            backend_code_parts
        )

        # Frontend Consolidation: Combine code, types, config, and static assets
        output_files["__code_mermaid_frontend.txt"] = join_blocks(
            frontend_code_parts + 
            frontend_types_parts +
            [b for b in frontend_config_parts if "package.json" in b or "vite.config.ts" in b or "tailwind.config.js" in b or "tsconfig" in b or "postcss.config.js" in b] + # Key frontend configs
            frontend_static_parts
        )

        # Config and Docs: Critical docs, root readme, structure, dda, etc.
        output_files["__code_mermaid_config_docs.txt"] = join_blocks(
            config_doc_parts + 
            [b for b in backend_config_parts if "requirements.txt" not in b and ".replit" not in b and "alembic.ini" not in b] + # Other backend configs
            [b for b in frontend_config_parts if "package.json" not in b and "vite.config.ts" not in b and "tailwind.config.js" not in b and "tsconfig" not in b and "postcss.config.js" not in b] # Other frontend configs
        )

        # Include tests and others if they exist
        if tests_parts:
            output_files["__code_mermaid_tests.txt"] = join_blocks(tests_parts)
        if other_parts:
            output_files["__code_mermaid_other.txt"] = join_blocks(other_parts)

        return output_files

class CompleteProfile(AnalysisProfile):
    """
    Profil d'analyse qui inclut la quasi-totalité des fichiers pour une analyse complète,
    ignorant uniquement les binaires non pertinents et les dossiers de développement/cache.
    """
    profile_id: str = "complet"
    profile_name: str = "Profil Complet (Tous les Fichiers)"

    # IGNORER les dossiers de développement, caches, binaires, lock files, et certains formats d'image
    IGNORED_DIRS_OR_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "node_modules", "dist", "build", "tests", "instance", "attached_assets"
    }
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "package-lock.json", "*.lock", "*.db", "*.sql", "*.log",
        "*.png", "*.ico", "*.svg", # Binary image files
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        filename_lower = path_components[-1].lower()

        # 1. Never ignore critical config/doc files.
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False
        # .env.example is critical as it shows what's needed.

        # 2. Ignore specific files and general patterns.
        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE:
            return True
        # Ensure general JSON files are ignored unless they are critical config (like package.json)
        if filename_lower.endswith(".json") and path_in_zip != "frontend/package.json":
            return True

        # 3. Ignore common development/build/cache directories.
        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        """
        Attribue la catégorie 'TOTAL' à tous les fichiers non ignorés.
        """
        return {"TOTAL"}

    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:
        """
        Génère un unique fichier consolidé avec tout le contenu.
        """
        def join_blocks(blocks: Iterable[str]) -> str:
            return "\n\n".join(blocks)

        total_parts = [
            block for block, categories in categorized_files if "TOTAL" in categories
        ]

        return {
            "__code_complet_total.txt": join_blocks(total_parts),
        }

# ==============================================================================
# 3. REGISTRE DES PROFILIS DISPONIBLES
# ==============================================================================

# Note: Le traceback NameError pour CodeToTextProfile était probablement dû à une version
# antérieure ou à un problème d'exécution/copie. L'ordre des définitions dans ce fichier
# est correct et CodeToTextProfile est défini avant d'être utilisé dans PROFILES.
# Ce fichier inclut maintenant le nouveau MermaidProfile.
PROFILES: dict[str, AnalysisProfile] = {
    p.profile_id: p for p in [
        AdminScolaireProfile(),
        ScenarioBuilderProfile(),
        CodeToTextProfile(),
        CompleteProfile(),
        MermaidProfile(), # NOUVEAU PROFIL AJOUTÉ
    ]
}