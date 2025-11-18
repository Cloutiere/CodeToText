# analysis_profiles.py
# [Version 2.2.6]

from __future__ import annotations

import abc
from collections.abc import Iterable
import os

# ==============================================================================
# IMPORT DE LA CLASSE DE BASE
# ==============================================================================
from codetotext_core.profiles.base import AnalysisProfile

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

    # Note : Les fichiers globaux (lockfiles, .db, images) sont gérés par AnalysisProfile.is_always_ignored
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "dump.sql", "db_dump.json",
        "budgets_a_importer.json", "import_prod_data_final.sh", "generate_schema.py",
    }

    BOILERPLATE_FILES: set[str] = {
        "migrations/README", "migrations/alembic.ini", "migrations/script.py.mako",
        "administration_scolaire_app/py.typed", "react_apps/sports_budget/index.html", "eslint.config.js",
        "react_apps/sports_budget/tailwind.temp.js", "administration_scolaire_app/taches/routes_backup.py",
        "administration_scolaire_app/taches/routes_merged.py", "administration_scolaire_app/taches/routes_with_duplicate.py",
        "administration_scolaire_app/taches/admin.py",
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        # 1. Priorité absolue : Inclusion forcée (DDA, Memos)
        if AnalysisProfile.is_always_included(path_in_zip, path_components):
            return False

        # 2. Priorité absolue : Exclusion forcée (Binaires, DB, Lockfiles globaux)
        if AnalysisProfile.is_always_ignored(path_in_zip, path_components):
            return True

        filename_lower = path_components[-1].lower()

        # 3. Règles spécifiques au profil
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False

        if filename_lower == "readme.md" and path_in_zip == "readme.md":
            return False

        # Extensions spécifiques à ce projet (non couvertes par le global)
        if filename_lower.endswith(".sql"): return True
        if filename_lower.endswith(".json") and filename_lower != "package.json":
            return True

        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE: return True

        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            if path_in_zip.startswith("administration_scolaire_app/migrations/versions/"):
                 return False
            return True

        if filename_lower.endswith(".md") and filename_lower != "readme.md": return True
        if path_in_zip in self.BOILERPLATE_FILES: return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = set()
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            categories.add("CONFIG_DOC")

        if path_in_zip.startswith("administration_scolaire_app/"):
            if path_in_zip.endswith(".py"):
                if "taches" in path_in_zip:
                    categories.add("TACHES")
                elif "finance" in path_in_zip or "journal_entry_service.py" in path_in_zip:
                    categories.add("FIN_GLOBAL")
                elif "api_sports.py" in path_in_zip or "services_sports_budget.py" in path_in_zip:
                    categories.add("FIN_SPORTIF")
                elif "app.py" in path_in_zip:
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
            categories.add("FIN_SPORTIF")

        elif path_in_zip.endswith(".md"):
            categories.add("CONFIG_DOC")

        elif path_in_zip.endswith(".ini"):
            categories.add("BACKEND_CONFIG")

        elif path_in_zip.endswith(".json"):
            if path_in_zip == "package.json":
                categories.add("FRONTEND_CONFIG")

        elif path_in_zip.startswith("frontend/"):
            if path_in_zip.endswith((".tsx", ".ts", ".jsx", ".js")):
                if "frontend/src/" in path_in_zip and not path_in_zip.endswith("vite-env.d.ts"):
                    categories.add("FRONTEND_CODE")
                else:
                    categories.add("FRONTEND_CONFIG")
            elif path_in_zip.endswith(".css"):
                categories.add("FRONTEND_STATIC")
            elif path_in_zip.endswith(".html"):
                categories.add("FRONTEND_STATIC")

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

        output_files["__code_admin_scolaire_taches.txt"] = join_blocks(taches_parts)
        output_files["__code_admin_scolaire_fin_global.txt"] = join_blocks(fin_global_parts)
        output_files["__code_admin_scolaire_fin_sportif.txt"] = join_blocks(fin_sportif_parts)

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

    IGNORED_DIRS_OR_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "instance", 
        "attached_assets", 
        "node_modules", "dist", "build", "tests"
    }

    # Note : poetry.lock, database.db, *.png, package-lock.json sont gérés globalement
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "lint.md", "replit.md", ".gitignore",
    }

    MIGRATIONS_BOILERPLATE: set[str] = {
        "README", "alembic.ini", "script.py.mako"
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        # 1. Priorité absolue : Inclusion forcée
        if AnalysisProfile.is_always_included(path_in_zip, path_components):
            return False

        # 2. Priorité absolue : Exclusion forcée (Binaires, DB, Lockfiles)
        if AnalysisProfile.is_always_ignored(path_in_zip, path_components):
            return True

        filename = path_components[-1]
        filename_lower = filename.lower()

        # 3. Règles spécifiques
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False

        if filename_lower == "readme.md" and path_in_zip == "readme.md":
            return False

        if filename_lower.endswith(".sql"): return True

        if filename_lower.endswith(".json"):
            if filename_lower == "package.json":
                return False
            if (path_in_zip.startswith("backend/seed_data/models/") or 
                path_in_zip.startswith("backend/seed_data/profiles/")):
                return False
            return True 

        if path_in_zip in self.SPECIFIC_FILES_TO_IGNORE: return True

        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            if path_in_zip.startswith("scenario_builder_app/migrations/versions/"):
                 return False
            return True

        if filename_lower.endswith(".md") and filename_lower != "readme.md": return True
        if path_in_zip in self.MIGRATIONS_BOILERPLATE: return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = set()
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            categories.add("CONFIG_DOC")

        if path_in_zip.endswith(".json") and (
            path_in_zip.startswith("backend/seed_data/models/") or 
            path_in_zip.startswith("backend/seed_data/profiles/")
        ):
            categories.add("AI_CONFIG")

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
            categories.add("FIN_SPORTIF")

        elif path_in_zip.endswith(".md"):
            categories.add("CONFIG_DOC")
        elif path_in_zip == "package.json":
            categories.add("FRONTEND_CONFIG")
        elif path_in_zip == "replit.md":
            categories.add("CONFIG_DOC")

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
        ai_config_parts = [b for b, c in categorized_files if "AI_CONFIG" in c]

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

        output_files["__code_scenario_builder_config_docs.txt"] = join_blocks(
            config_doc_parts + ai_config_parts + backend_core_parts + backend_config_parts +
            backend_util_parts + frontend_code_parts + frontend_static_parts +
            frontend_config_parts
        )

        if tests_parts:
            output_files["__code_scenario_builder_tests.txt"] = join_blocks(tests_parts)
        if other_parts:
            output_files["__code_scenario_builder_other.txt"] = join_blocks(other_parts)

        return output_files

class CodeToTextProfile(AnalysisProfile):
    """
    Profil d'analyse pour le projet CodeToText lui-même.
    """
    profile_id: str = "codetotext"
    profile_name: str = "Projet : CodeToText (Auto-Analyse)"

    IGNORED_PATH_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "instance", "node_modules", "dist", "build"
    }
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        ".gitignore"
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        # 1. Inclusion forcée
        if AnalysisProfile.is_always_included(path_in_zip, path_components):
            return False

        # 2. Exclusion forcée (Global garbage)
        if AnalysisProfile.is_always_ignored(path_in_zip, path_components):
            return True

        filename = path_components[-1]
        filename_lower = filename.lower()

        # Protection fichiers critiques de l'app
        if filename in ["app.py", "analysis_profiles.py", "replit.md", "pyproject.toml"]:
             return False

        if any(comp in self.IGNORED_PATH_COMPONENTS for comp in path_components):
            if "templates" in path_components and filename.endswith(".html"):
                return False
            return True

        if filename in self.SPECIFIC_FILES_TO_IGNORE:
            return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        _, ext = os.path.splitext(path_in_zip)

        if path_in_zip in ["app.py", "analysis_profiles.py"]:
            return {"BACKEND_CORE"}

        if path_in_zip.endswith(".py"):
            return {"BACKEND_UTIL"}

        if path_in_zip.startswith("templates/") and ext == ".html":
            return {"FRONTEND_JINJA"}

        if path_in_zip in ["pyproject.toml", "replit.md"]:
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

class MermaidProfile(AnalysisProfile):
    """Profil d'analyse pour le projet Mermaid Editor."""
    profile_id: str = "mermaid"
    profile_name: str = "Projet : Mermaid Editor"

    IGNORED_DIRS_OR_COMPONENTS: set[str] = {
        ".git", ".github", ".ruff_cache", "__pycache__", "venv",
        "node_modules", "dist", "build", "instance", "attached_assets",
        "migrations/versions"
    }

    # Note : binaires, lockfiles sont gérés globalement
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        ".gitignore",
        "*.log", 
    }

    CRITICAL_CONFIG_FILES: set[str] = {
        ".env.example", 
        "AMELIORATIONS_COMPLETEES.md", 
        "CONFIGURATION_COMPLETE.md", 
        "SPECIFICATION_FONCTIONNELLE_V4.0.md",
        "MEMO_TECH_4.0.md",
        "MEMO_TECH_1.0.md", 
        "DDA_V4.0.md", 
        "DDA_V1.0.md", 
        "PLAN_DEVELOPPEMENT_FRONTEND.md", 
        "README.md", "STRUCTURE.md", "replit.md", ".replit",
        "backend/run.py",
        "backend/app/__init__.py", "backend/app/config.py", "backend/app/models.py",
        "backend/app/schemas.py", "backend/requirements.txt",
        "backend/migrations/alembic.ini",
        "backend/app/routes/mermaid.py", 
        "backend/app/services/mermaid_parser.py", "backend/app/services/mermaid_generator.py",
        "backend/app/routes/nodes.py", 
        "backend/app/routes/subprojects.py", 
        "backend/app/services/nodes.py",
        "backend/app/services/subprojects.py",
        "frontend/package.json",
        "frontend/vite.config.ts",
        "frontend/tailwind.config.js",
        "frontend/tsconfig.json",
        "frontend/tsconfig.node.json",
        "frontend/postcss.config.js",
        "frontend/src/types/api.ts", 
        "frontend/src/App.tsx", "frontend/src/main.tsx",
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        # 1. Inclusion forcée
        if AnalysisProfile.is_always_included(path_in_zip, path_components):
            return False

        # 2. Exclusion forcée (Global)
        if AnalysisProfile.is_always_ignored(path_in_zip, path_components):
            return True

        filename = path_components[-1]
        filename_lower = filename.lower()

        # 3. Règles spécifiques
        if path_in_zip in self.CRITICAL_CONFIG_FILES:
            return False

        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE:
            return True

        if filename_lower.endswith(".json") and path_in_zip != "frontend/package.json":
            return True

        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            if path_in_zip.startswith("backend/migrations/versions/"):
                return False
            return True

        if "tests" in path_components:
            return False

        if filename_lower.endswith(".md"):
            return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        categories = set()

        if path_in_zip in self.CRITICAL_CONFIG_FILES:
            categories.add("CONFIG_DOC")

        if path_in_zip.startswith("backend/"):
            if path_in_zip.endswith(".py"):
                if path_in_zip.startswith("backend/tests/"):
                    categories.add("TESTS")
                elif "routes" in path_in_zip:
                    if "mermaid.py" in path_in_zip: categories.add("BACKEND_CODE_CRITICAL")
                    elif "nodes.py" in path_in_zip or "subprojects.py" in path_in_zip:
                         categories.add("BACKEND_CODE_CRITICAL")
                    else: categories.add("BACKEND_CODE")
                elif "services" in path_in_zip:
                    if "mermaid_parser.py" in path_in_zip or "mermaid_generator.py" in path_in_zip:
                        categories.add("BACKEND_SERVICES_CRITICAL")
                    elif "nodes.py" in path_in_zip or "subprojects.py" in path_in_zip:
                        categories.add("BACKEND_CODE_CRITICAL")
                    else:
                        categories.add("BACKEND_CODE")
                elif "models.py" in path_in_zip or "schemas.py" in path_in_zip:
                    categories.add("BACKEND_CORE")
                elif "run.py" in path_in_zip or "__init__.py" in path_in_zip or "config.py" in path_in_zip:
                    categories.add("BACKEND_CORE")
                elif path_in_zip.startswith("backend/migrations/"):
                    categories.add("BACKEND_MIGRATIONS")
                else:
                    categories.add("BACKEND_UTIL") 
            elif path_in_zip == "backend/requirements.txt":
                 categories.add("BACKEND_CONFIG")
            elif path_in_zip.startswith("backend/migrations/") and os.path.splitext(path_in_zip)[1].lower() == ".ini":
                 categories.add("BACKEND_CONFIG")
            elif path_in_zip == "backend/.replit":
                 categories.add("CONFIG_DOC")

        elif path_in_zip.startswith("frontend/"):
            if path_in_zip.endswith((".tsx", ".ts", ".jsx", ".js")):
                if "frontend/src/" in path_in_zip:
                    if "frontend/src/types/api.ts" in path_in_zip: categories.add("FRONTEND_TYPES")
                    elif "frontend/src/App.tsx" in path_in_zip or "frontend/src/main.tsx" in path_in_zip: categories.add("FRONTEND_CODE")
                    else: categories.add("FRONTEND_CODE")
                else:
                    categories.add("FRONTEND_CONFIG")
            elif path_in_zip.endswith(".css"):
                categories.add("FRONTEND_STATIC")
            elif path_in_zip.endswith(".html"):
                categories.add("FRONTEND_STATIC")
            elif path_in_zip == "frontend/package.json":
                categories.add("FRONTEND_CONFIG")
            elif path_in_zip in ["frontend/vite.config.ts", "frontend/tailwind.config.js", "frontend/tsconfig.json", "frontend/tsconfig.node.json", "frontend/postcss.config.js"]:
                categories.add("FRONTEND_CONFIG")

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
        backend_code_critical_parts = [b for b, c in categorized_files if "BACKEND_CODE_CRITICAL" in c]
        backend_services_critical_parts = [b for b, c in categorized_files if "BACKEND_SERVICES_CRITICAL" in c]

        backend_code_parts = [
            b for b, c in categorized_files 
            if "BACKEND_CODE" in c and not (
                "BACKEND_CORE" in c or "BACKEND_CONFIG" in c or "BACKEND_MIGRATIONS" in c or 
                "BACKEND_CODE_CRITICAL" in c or "BACKEND_SERVICES_CRITICAL" in c
            )
        ]

        frontend_code_parts = [b for b, c in categorized_files if "FRONTEND_CODE" in c]
        frontend_static_parts = [b for b, c in categorized_files if "FRONTEND_STATIC" in c]
        frontend_config_parts = [b for b, c in categorized_files if "FRONTEND_CONFIG" in c]
        frontend_types_parts = [b for b, c in categorized_files if "FRONTEND_TYPES" in c]

        config_doc_parts = [b for b, c in categorized_files if "CONFIG_DOC" in c]
        tests_parts = [b for b, c in categorized_files if "TESTS" in c]
        other_parts = [b for b, c in categorized_files if "OTHER" in c]

        output_files = {}

        all_parts_no_tests = (
            config_doc_parts + 
            backend_core_parts + 
            backend_config_parts + 
            backend_code_critical_parts + 
            backend_services_critical_parts + 
            backend_code_parts + 
            frontend_code_parts + 
            frontend_types_parts + 
            frontend_config_parts + 
            frontend_static_parts +
            other_parts
        )
        output_files["__code_mermaid_complet_sans_tests.txt"] = join_blocks(all_parts_no_tests)

        all_parts = all_parts_no_tests + tests_parts
        output_files["__code_mermaid_complet.txt"] = join_blocks(all_parts)

        output_files["__code_mermaid_backend.txt"] = join_blocks(
            backend_core_parts + 
            [b for b in backend_config_parts if "requirements.txt" in b or ".replit" in b] + 
            backend_code_critical_parts + 
            backend_services_critical_parts + 
            backend_code_parts
        )

        output_files["__code_mermaid_frontend.txt"] = join_blocks(
            frontend_code_parts + 
            frontend_types_parts +
            [b for b in frontend_config_parts if "package.json" in b or "vite.config.ts" in b or "tailwind.config.js" in b or "tsconfig" in b or "postcss.config.js" in b] + 
            frontend_static_parts
        )

        remaining_backend_configs = [b for b in backend_config_parts if "requirements.txt" not in b and ".replit" not in b]
        remaining_frontend_configs = [b for b in frontend_config_parts if "package.json" not in b and "vite.config.ts" not in b and "tailwind.config.js" not in b and "tsconfig" not in b and "postcss.config.js" not in b]

        output_files["__code_mermaid_config_docs.txt"] = join_blocks(
            config_doc_parts + 
            remaining_backend_configs + 
            remaining_frontend_configs
        )

        if tests_parts:
            output_files["__code_mermaid_tests.txt"] = join_blocks(tests_parts)
        if other_parts:
            output_files["__code_mermaid_other.txt"] = join_blocks(other_parts)

        return output_files

class CompleteProfile(AnalysisProfile):
    """
    Profil d'analyse qui inclut la quasi-totalité des fichiers pour une analyse complète.
    """
    profile_id: str = "complet"
    profile_name: str = "Profil Complet (Tous les Fichiers)"

    # IGNORER les dossiers de développement, caches, binaires, lock files
    IGNORED_DIRS_OR_COMPONENTS: set[str] = {
        ".git", ".ruff_cache", "__pycache__", "venv",
        "node_modules", "dist", "build", "instance", "attached_assets"
    }

    # Note: Lockfiles, .db, .png gérés globalement
    SPECIFIC_FILES_TO_IGNORE: set[str] = {
        "*.log"
    }

    def is_file_ignored(self, path_in_zip: str, path_components: list[str]) -> bool:
        # 1. Inclusion forcée
        if AnalysisProfile.is_always_included(path_in_zip, path_components):
            return False

        # 2. Exclusion forcée (Global)
        if AnalysisProfile.is_always_ignored(path_in_zip, path_components):
            return True

        filename_lower = path_components[-1].lower()

        # 3. Règles spécifiques
        if path_in_zip in AnalysisProfile.CRITICAL_CONFIG_BASENAMES:
            return False

        if filename_lower in self.SPECIFIC_FILES_TO_IGNORE:
            return True

        if filename_lower.endswith(".json") and path_in_zip != "frontend/package.json":
            return True

        if any(comp in self.IGNORED_DIRS_OR_COMPONENTS for comp in path_components):
            return True

        return False

    def categorize_file(self, path_in_zip: str) -> set[str]:
        return {"TOTAL"}

    def generate_consolidated_files(
        self, categorized_files: list[tuple[str, set[str]]]
    ) -> dict[str, str]:
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

PROFILES: dict[str, AnalysisProfile] = {
    p.profile_id: p for p in [
        AdminScolaireProfile(),
        ScenarioBuilderProfile(),
        CodeToTextProfile(),
        CompleteProfile(),
        MermaidProfile(),
    ]
}