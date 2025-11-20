# app.py
# [Version 8.3]

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
from analysis_profiles import PROFILES
# Import de la classe de base depuis le nouveau module core
from codetotext_core.profiles.base import AnalysisProfile
# Import des fonctions utilitaires depuis le nouveau module core
from codetotext_core.utils.file_utils import get_language_from_filename, generate_zip_tree

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

            # --- ÉTAPE 1 : GATEKEEPER P_1 (Exclusion Impérative) ---
            if AnalysisProfile.is_always_ignored(path_for_filtering, path_components):
                continue  # Skip précoce des fichiers "garbage"
            # --- FIN DU GATEKEEPER ---

            # --- ÉTAPE 2 : LOGIQUE MÉTIER DU PROFIL ---
            if profile.is_file_ignored(path_for_filtering, path_components):
                continue  # Filtrage spécifique au projet
            # --- FIN LOGIQUE MÉTIER ---

            # Logique de filtrage générique restante
            if filename_basename.startswith(".") and filename_basename != '.replit':
                continue
            if not keep_original_extension and filename_basename_lower.endswith(".txt"):
                continue

            content = zin.read(item.filename)
            path_for_display = path_for_filtering

            new_filename_base = path_for_display.replace('/', '.') if basename_counts[filename_basename] > 1 else filename_basename

            # AC-3 + P_2 : Liste blanche des extensions critiques
            # Assure la conservation des extensions même en mode textifié
            extensions_to_keep = {".tsx", ".css", ".html", ".js", ".json", ".py", ".md"}
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

            # --- ÉTAPE 3 : CONTRÔLE DE CONCATÉNATION P_4 ---
            # Exclut les documents d'architecture des consolidations
            is_architecture_doc = AnalysisProfile.is_always_included(path_for_filtering, path_components)
            if not is_architecture_doc:  # Condition P_4
                try:
                    file_content_str = content.decode('utf-8', errors='replace')
                    language = get_language_from_filename(filename_basename)
                    file_block = f"-- DEBUT DU FICHIER --\nChemin: {path_for_display}\nLangage: {language}\n-- CONTENU DU CODE --\n{file_content_str}\n-- FIN DU FICHIER --\n"
                    full_code_content_parts.append(file_block)
                    if not filename_basename_lower.endswith('.css'):
                        full_code_sans_css_parts.append(file_block)

                    # Délégation au profil pour la catégorisation (seulement si pas un doc d'architecture)
                    categories = profile.categorize_file(path_for_filtering)
                    categorized_files.append((file_block, categories))

                except Exception as e:
                    app.logger.error(f"Erreur préparation contenu de {full_path_in_zip}: {e}")
            # --- FIN CONTRÔLE P_4 ---

        if not full_code_content_parts:
            raise ValueError("Le fichier ZIP ne contenait aucun fichier traitable après filtrage.")

        zout.writestr("__arborescence.txt", tree_content.encode('utf-8'))
        tree_block_for_code_complet = f"--- DEBUT DE L'ARBORESCENCE ---\n{tree_content}\n--- FIN DE L'ARBORESCENCE ---\n"
        final_full_code_content = [tree_block_for_code_complet] + full_code_content_parts
        zout.writestr("__code_complet.txt", "\n".join(final_full_code_content).encode('utf-8'))
        zout.writestr("__code_complet_sans_CSS.txt", "\n".join(full_code_sans_css_parts).encode('utf-8'))

        # Délégation au profil pour les fichiers consolidés
        consolidated_files = profile.generate_consolidated_files(categorized_files)
        for filename, content in consolidated_files.items():
            zout.writestr(filename, content.encode("utf-8"))

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
            server_filename = user_facing_filename  # Pas d'UUID, juste le timestamp
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
        app.config["DOWNLOAD_FOLDER"],
        server_filename,
        as_attachment=True,
        download_name=user_filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)