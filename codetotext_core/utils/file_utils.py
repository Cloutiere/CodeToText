# codetotext_core/utils/file_utils.py
# [Version 2.0]

from __future__ import annotations

import io
import os
from collections import Counter
import zipfile

def get_language_from_filename(filename: str) -> str:
    """Détermine le langage de programmation à partir de l'extension du fichier."""
    extension_map = {
        ".py": "Python", ".js": "JavaScript", ".html": "HTML", ".css": "CSS",
        ".java": "Java", ".cs": "C#", ".cpp": "C++", ".c": "C", ".go": "Go",
        ".rb": "Ruby", ".php": "PHP", ".rs": "Rust", ".kt": "Kotlin",
        ".ts": "TypeScript", ".tsx": "TypeScript React", ".sql": "SQL",
        ".sh": "Shell", ".bat": "Batch", ".json": "JSON", ".xml": "XML",
        ".yml": "YAML", ".yaml": "YAML", ".md": "Markdown", ".replit": "Replit Config",
        ".toml": "TOML", ".pyi": "Python Stub", ".jsm": "JavaScript Module",
    }
    _, ext = os.path.splitext(filename)
    if not ext and filename.lower() in ["dockerfile"]:
        return "Dockerfile"
    return extension_map.get(ext.lower(), f"Inconnu ({ext})")


def generate_zip_tree(zip_file_stream: io.BytesIO) -> str:
    """Génère une représentation textuelle de l'arborescence d'un fichier ZIP."""
    if not zip_file_stream:
        return "Le flux du fichier ZIP est vide."
    tree_lines: list[str] = []
    try:
        with zipfile.ZipFile(zip_file_stream, "r") as zin:
            all_paths = sorted([info.filename for info in zin.infolist()])
            if not all_paths:
                return "Le fichier ZIP est vide."

            root_name = ""
            if all_paths:
                first_part = all_paths[0].split('/')[0]
                if all(p.startswith(first_part + '/') or p == first_part for p in all_paths):
                    root_name = first_part

            structure: dict = {}
            for path in all_paths:
                path_to_process = path
                if root_name:
                    path_to_process = path[len(root_name) + 1:] if path.startswith(root_name + '/') else path
                    if not path_to_process: continue

                parts = path_to_process.split("/")
                current_level = structure
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

            def build_tree_lines(dir_structure: dict, prefix: str = "") -> list[str]:
                lines: list[str] = []
                items = sorted(list(dir_structure.keys()))
                for i, name in enumerate(items):
                    connector = "└── " if i == len(items) - 1 else "├── "
                    lines.append(f"{prefix}{connector}{name}")
                    if dir_structure.get(name):
                        extension = "    " if i == len(items) - 1 else "│   "
                        lines.extend(build_tree_lines(dir_structure[name], prefix + extension))
                return lines

            if root_name:
                tree_lines.append(root_name)
                tree_lines.extend(build_tree_lines(structure, "│   "))
            else:
                tree_lines.extend(build_tree_lines(structure))

    except zipfile.BadZipFile:
        return "Erreur : Le fichier fourni n'est pas un ZIP valide."
    except Exception as e:
        # NOTE: Le logger Flask n'est pas disponible ici. L'appelant doit gérer l'exception.
        # Pour maintenir la compatibilité, on lève une RuntimeError avec le message d'origine.
        raise RuntimeError(f"Erreur lors de la génération de l'arbre : {e}")
    return "\n".join(tree_lines)