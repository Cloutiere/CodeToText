# [app.py]
# [Version 8.1]

from __future__ import annotations

import io
import os
import uuid
import zipfile
from collections import Counter
from datetime import datetime

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

# Importation du système de profils
from analysis_profiles import PROFILES, AnalysisProfile

app = Flask(__name__, template_folder='templates', instance_relative_config=True)
app.secret_key = "supersecretkey"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

DOWNLOAD_FOLDER = os.path.join(app.instance_path, "downloads")
app.config["DOWNLOAD_FOLDER"] = DOWNLOAD_FOLDER
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"zip"}


def allowed_file(filename: str) -> bool:
    """Vérifie si l'extension du fichier est autorisée."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
        app.logger.error(f"Erreur lors de la génération de l'arbre : {e}")
        return "Une erreur interne est survenue."
    return "\n".join(tree_lines)


def _process_zip_file(
    input_zip_stream: io.BytesIO,
    uploaded_filename: str,
    keep_original_extension: bool,
    tree_content: str,
    profile: AnalysisProfile,  # Le profil est maintenant un paramètre
) -> tuple[io.BytesIO, str]:
    """
    Traite un fichier ZIP en utilisant le profil d'analyse fourni.
    """
    output_zip_stream = io.BytesIO()
    with zipfile.ZipFile(input_zip_stream, "r") as zin, zipfile.ZipFile(output_zip_stream, "w", zipfile.ZIP_DEFLATED) as zout:
        all_file_paths_in_zip = [item.filename for item in zin.infolist() if not item.is_dir()]
        common_prefix_to_remove = ""
        if all_file_paths_in_zip:
            first_path_parts = all_file_paths_in_zip[0].split('/', 1)
            if len(first_path_parts) > 1 and first_path_parts[0]:
                potential_common_dir = first_path_parts[0] + '/'
                if all(p.startswith(potential_common_dir) for p in all_file_paths_in_zip):
                    common_prefix_to_remove = potential_common_dir

        basename_counts = Counter(item.filename.split('/')[-1] for item in zin.infolist() if not item.is_dir())
        full_code_content_parts, full_code_sans_css_parts, categorized_files = [], [], []

        for item in zin.infolist():
            if item.is_dir():
                continue
            full_path_in_zip = item.filename
            path_for_filtering = full_path_in_zip.replace(common_prefix_to_remove, "", 1).replace('\\', '/')
            path_components = path_for_filtering.split('/')
            filename_basename, filename_basename_lower = path_components[-1], path_components[-1].lower()

            # --- DÉLÉGATION AU PROFIL ---
            if profile.is_file_ignored(path_for_filtering, path_components):
                continue
            # --- FIN DE LA DÉLÉGATION ---

            # Logique de filtrage générique restante
            if filename_basename.startswith(".") and filename_basename != '.replit':
                continue
            if not keep_original_extension and filename_basename_lower.endswith(".txt"):
                continue

            content = zin.read(item.filename)
            path_for_display = path_for_filtering

            new_filename_base = path_for_display.replace('/', '.') if basename_counts[filename_basename] > 1 else filename_basename

            # AC-3: Ajout de ".py" à la liste des extensions à conserver même en mode textifié.
            extensions_to_keep = {".tsx", ".css", ".html", ".js", ".json", ".py"}
            _, ext = os.path.splitext(filename_basename_lower)

            if keep_original_extension or ext in extensions_to_keep or filename_basename_lower in ["package.json"]:
                new_filename_in_zip = new_filename_base
            else:
                new_filename_in_zip = new_filename_base + ".txt"

            if filename_basename_lower == "synthèse_développement.md":
                new_filename_in_zip = new_filename_base
            elif filename_basename_lower == ".replit":
                new_filename_in_zip = "replit.txt"

            zout.writestr(new_filename_in_zip, content)

            if filename_basename_lower != "synthèse_développement.md":
                try:
                    file_content_str = content.decode('utf-8', errors='replace')
                    language = get_language_from_filename(filename_basename)
                    file_block = f"-- DEBUT DU FICHIER --\nChemin: {path_for_display}\nLangage: {language}\n-- CONTENU DU CODE --\n{file_content_str}\n-- FIN DU FICHIER --"
                    full_code_content_parts.append(file_block)
                    if not filename_basename_lower.endswith('.css'):
                        full_code_sans_css_parts.append(file_block)

                    # --- DÉLÉGATION AU PROFIL ---
                    categories = profile.categorize_file(path_for_filtering)
                    categorized_files.append((file_block, categories))
                    # --- FIN DE LA DÉLÉGATION ---

                except Exception as e:
                    app.logger.error(f"Erreur préparation contenu de {full_path_in_zip}: {e}")

        if not full_code_content_parts:
            raise ValueError("Le fichier ZIP ne contenait aucun fichier traitable après filtrage.")

        zout.writestr("__arborescence.txt", tree_content.encode('utf-8'))
        tree_block_for_code_complet = f"--- DEBUT DE L'ARBORESCENCE ---\n{tree_content}\n--- FIN DE L'ARBORESCENCE ---"
        final_full_code_content = [tree_block_for_code_complet] + full_code_content_parts
        zout.writestr("__code_complet.txt", "\n\n".join(final_full_code_content).encode('utf-8'))
        zout.writestr("__code_complet_sans_CSS.txt", "\n\n".join(full_code_sans_css_parts).encode('utf-8'))

        # --- DÉLÉGATION AU PROFIL ---
        consolidated_files = profile.generate_consolidated_files(categorized_files)
        for filename, content in consolidated_files.items():
            zout.writestr(filename, content.encode("utf-8"))
        # --- FIN DE LA DÉLÉGATION ---

    output_zip_stream.seek(0)
    original_zip_name_base, _ = os.path.splitext(uploaded_filename)
    suffix_zip = "_flat_orig_ext.zip" if keep_original_extension else "_flat_textified.zip"
    base_output_filename = f"{original_zip_name_base}{suffix_zip}"
    return output_zip_stream, base_output_filename


@app.route("/", methods=["GET", "POST"])
def index():
    """Route principale de l'application."""
    available_profiles = list(PROFILES.values())

    if request.method == "POST":
        if 'file' not in request.files:
            flash("Aucun champ de fichier dans la requête.", "error")
            return redirect(request.url)

        file = request.files['file']
        profile_id = request.form.get("analysis_profile")

        if not file or not file.filename:
            flash("Aucun fichier sélectionné.", "error")
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash("Type de fichier non autorisé. Veuillez téléverser un fichier ZIP.", "error")
            return redirect(request.url)
        if not profile_id:
            flash("Veuillez sélectionner un profil d'analyse.", "error")
            return redirect(request.url)

        profile = PROFILES.get(profile_id)
        if not profile:
            flash(f"Profil d'analyse inconnu : {profile_id}.", "error")
            return redirect(request.url)

        try:
            keep_original_extension = request.form.get("keep_original_extension") == "true"
            file_bytes = file.read()
            tree_stream, process_stream = io.BytesIO(file_bytes), io.BytesIO(file_bytes)
            tree_output = generate_zip_tree(tree_stream)

            # Appel à la fonction de traitement en passant le profil sélectionné
            processed_stream, base_output_filename = _process_zip_file(
                process_stream, file.filename, keep_original_extension, tree_output, profile
            )

            timestamp = datetime.now().strftime("%y-%m-%d_%Hh%M")
            name_root, extension = os.path.splitext(base_output_filename)
            user_facing_filename = f"{name_root}_{timestamp}{extension}"
            server_filename = f"{uuid.uuid4()}_{base_output_filename}"
            save_path = os.path.join(app.config['DOWNLOAD_FOLDER'], server_filename)
            with open(save_path, 'wb') as f:
                f.write(processed_stream.getbuffer())

            download_info = {
                "url": url_for('download_file', server_filename=server_filename, user_filename=user_facing_filename),
                "filename": user_facing_filename
            }

            flash("Traitement réussi ! Vous pouvez télécharger le fichier et consulter l'arborescence.", "success")
            return render_template("index.html", tree_output=tree_output, download_info=download_info, profiles=available_profiles)

        except (zipfile.BadZipFile, ValueError) as e:
            flash(str(e), "error")
        except Exception as e:
            app.logger.error(f"Erreur inattendue : {e}", exc_info=True)
            flash("Une erreur interne est survenue.", "error")

        return redirect(request.url)

    return render_template("index.html", profiles=available_profiles)


@app.route("/download/<path:server_filename>")
def download_file(server_filename: str):
    """Route pour le téléchargement des fichiers traités."""
    user_filename = request.args.get('user_filename', server_filename)
    return send_from_directory(
        app.config['DOWNLOAD_FOLDER'],
        server_filename,
        as_attachment=True,
        download_name=user_filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)