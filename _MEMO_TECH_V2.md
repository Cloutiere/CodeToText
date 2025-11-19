**MÉMO TECHNIQUE**

**Objet : Implémentation des Directives du DDA V1.0 - Amélioration du Moteur de Filtrage (AC-1, AC-2, AC-3)**

**À :** Équipe de Développement et d'Architecture Logicielle
**De :** Architecte Logiciel Sénior
**Date :** 17 novembre 2025
**Version DDA Référencée :** DDA V1.0 (Amélioration du Moteur de Filtrage)

---

### 1. Synthèse des Objectifs

Ce mémo technique formalise la mise en œuvre des trois directives d'amélioration du moteur de filtrage, issues du Document de Décision d'Architecture (DDA) V1.0. Ces ajustements visent à optimiser l'exhaustivité de l'analyse et la convivialité des livrables générés.

| Directive DDA | Description Fonctionnelle | Impact technique principal |
| :--- | :--- | :--- |
| **AC-1** | `CompleteProfile` inclut désormais les dossiers `tests/` et `.github/`. | Augmentation de la portée d'analyse pour le profil le plus exhaustif. |
| **AC-2** | Inclusion systématique du fichier critique `.replit`. | Garantit la disponibilité du contexte d'exécution du projet. |
| **AC-3** | Conservation systématique de l'extension `.py`. | Amélioration de la lisibilité des livrables de code source Python en mode "textifié". |

---

### 2. Modifications Techniques Détailées

#### 2.1. Fichier : `analysis_profiles.py` (Mise à jour du Strategy Pattern)

| Directive | Implémentation technique | Justification |
| :--- | :--- | :--- |
| **AC-1** | Dans la classe `CompleteProfile`, retrait de `"tests"` et `".github"` de l'ensemble `IGNORED_DIRS_OR_COMPONENTS`. | L'objectif du profil `complet` est l'exhaustivité ; les stratégies de CI/CD et de test sont désormais des éléments de code source à inclure. |
| **AC-2** | Dans la méthode `CodeToTextProfile.is_file_ignored`, suppression du bloc d'exclusion explicite de `.replit`. | `.replit` étant listé dans `AnalysisProfile.CRITICAL_CONFIG_BASENAMES`, la suppression de la règle d'ignorance spécifique permet de garantir son inclusion par la règle d'or d'inclusion des fichiers critiques. |

#### 2.2. Fichier : `app.py` (Mise à jour du Traitement ZIP)

| Directive | Implémentation technique | Justification |
| :--- | :--- | :--- |
| **AC-3** | Dans la fonction `_process_zip_file`, ajout de `".py"` à l'ensemble `extensions_to_keep`. | Assure que les fichiers Python (considérés comme du code source primaire) conservent leur extension d'origine dans le ZIP de sortie, même si le mode `keep_original_extension=False` est sélectionné. |

---

### 3. Garde-fou Architectural Critique (SDK Google AI)

Conformément à la section 3.b du DDA, un rappel strict des conventions du SDK est obligatoire pour tout développement futur impliquant l'intégration de modèles d'IA.

*   **SDK Exclusif :** `google-genai` (et non l'ancien `google-generativeai`).
*   **Patron d'Appel Obligatoire :** `client = genai.Client()` suivi de `client.models.generate_content(...)`.
*   **Interdiction Formelle :** L'utilisation de `genai.GenerativeModel()` est interdite.
*   **Configuration :** La configuration doit être passée directement via `config={...}` ou des arguments nommés, et **jamais** via une clé `generation_config`.

**Point de Vigilance :** La base de connaissances des outils LLMs a une tendance prouvée à la régression vers les anciens patrons d'API. L'équipe doit activement valider la syntaxe via la documentation officielle avant tout déploiement de code AI.