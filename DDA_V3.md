# Document de Décision d'Architecture (DDA) : V3 - Purification et Consolidation du Contexte

**Date :** 18 Novembre 2025
**Version :** 3.0 (Intégration du Filtrage Impératif et de l'Exclusion Contextuelle)
**Statut :** Prêt pour l'implémentation

---

## 1. Rappel des Exigences Structurantes

L'architecture est définie pour atteindre un équilibre optimal entre l'exhaustivité du contexte structurel et la pureté du contenu textuel pour l'analyse.

| Exigence | Description | Règle Architecturale Cible |
| :--- | :--- | :--- |
| **P_1 : Pureté du Contenu** | Exclusion impérative (Gatekeeper) des fichiers considérés comme du "Garbage" (binaires, lockfiles, minifiés). | Logique centralisée dans `AnalysisProfile.is_always_ignored`. |
| **P_2 : Fidélité des Formats** | Conservation de l'extension d'origine des fichiers Markdown (`.md`) dans le ZIP de sortie. | Ajout de `.md` à la liste blanche (`extensions_to_keep`). |
| **P_3 : Intégrité Structurelle** | L'arborescence (`__arborescence.txt`) doit lister **TOUS** les fichiers, y compris le Garbage exclu (P_1). | Le processus de génération d'arbre doit précéder le filtrage. |
| **P_4 : Anti-Pollution (NOUVELLE)** | Les documents d'architecture (DDA\_\*.md, MEMO\_TECH\_\*.md) doivent être des fichiers distincts, mais leur *contenu* doit être exclu des blocs de code consolidés (`__code_complet.txt`, etc.). | Contrôle conditionnel lors de la concaténation de contenu. |

## 2. Architecture Globale : Le Pipeline de Traitement Durci

L'architecture **Monolithe Modulaire** existante (Flask + `codetotext_core`) est maintenue. La robustesse est assurée par l'ordre d'exécution du pipeline dans la fonction centrale `_process_zip_file`.

### Schéma du Pipeline de Traitement de Fichier

Pour chaque fichier trouvé dans le ZIP :

1.  **Préparation :** Calcul des `path_for_filtering` et `path_components`.
2.  **Gatekeeper (P_1) :** Appel à `AnalysisProfile.is_always_ignored()`.
    *   *Si VRAI (Garbage) :* **STOP**. Passer au fichier suivant. (Gagne temps CPU/I/O en évitant la lecture).
3.  **Contrôle de Profil (Logique Métier) :** Appel à `profile.is_file_ignored()`.
    *   *Si VRAI (Profil spécifique) :* **STOP**. Passer au fichier suivant.
4.  **Lecture :** Lecture du contenu du fichier dans un buffer (`content = zin.read(...)`).
5.  **Détermination du Nom (P_2) :** Calcul de `new_filename_in_zip` (Intégration de la règle `.md` non-textifié).
6.  **Écriture Fichier Distinct :** `zout.writestr(new_filename_in_zip, content)`. (Le fichier existe toujours dans le ZIP de sortie).
7.  **Contrôle de Concaténation (P_4) :** Appel à `AnalysisProfile.is_always_included()`.
    *   *Si VRAI (DDA/MEMO) :* **SKIP** la création de `file_block` et l'ajout aux listes de consolidation.
    *   *Si FAUX :* Créer le `file_block` et l'ajouter aux listes (`full_code_content_parts`, `categorized_files`).
8.  **Fin de Boucle.**

## 3. Stack Technologique & Justifications

| Composant | Technologie | Justification |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+ / Flask | Infrastructure légère et éprouvée pour le traitement transactionnel I/O intensif (ZIP). |
| **Data (In-memory)** | `zipfile`, `io.BytesIO` | Garantit un traitement `stateless` (sans écriture disque intermédiaire) et la sécurité. |
| **Filtrage** | `set` (ensembles Python) | Performance O(1) pour les lookups d'extensions et de noms dans les listes noires critiques. |

### Dépendances Critiques et Versions Cibles (Rappel de Vigilance)

*   **SDK Google AI :** Le projet doit utiliser **exclusivement** le SDK `google-genai` (v1.0+).
*   **Contrainte d'usage :** Toute intégration doit passer par `client = genai.Client()` et `client.models.generate_content(...)`. L'utilisation de patrons obsolètes (`genai.GenerativeModel()`) est formellement interdite pour des raisons de compatibilité et de dérive des LLMs.

## 4. Principes de Conception

### 4.1. Implémentation du Gatekeeper (P_1)

Le fichier `codetotext_core/profiles/base.py` doit être mis à jour :

*   **Ajout :** Création d'une nouvelle constante `CRITICAL_IGNORED_SUFFIXES: set[str] = {".min.js", ".min.css", ".map"}`.
*   **Mise à jour de `AnalysisProfile.is_always_ignored` :**
    1.  Vérifie `CRITICAL_IGNORED_BASENAMES` (match exact, ex: `poetry.lock`).
    2.  Vérifie `CRITICAL_IGNORED_EXTENSIONS` (match extension, ex: `.png`).
    3.  **NOUVEAU :** Vérifie `CRITICAL_IGNORED_SUFFIXES` (match fin de chaîne, ex: `filename.lower().endswith(suffix)`).

### 4.2. Préservation des Extensions (P_2)

Le fichier `app.py` (ou `zip_processor.py`) doit être mis à jour :

*   **Mise à jour de `extensions_to_keep` :** La liste blanche doit inclure explicitement **`.md`** (en plus de `.py`, `.js`, etc.) pour court-circuiter le renommage en `.txt`.

### 4.3. Contrôle de Concaténation (P_4)

Le fichier `app.py` (dans `_process_zip_file`) doit être mis à jour pour exploiter la logique existante d'inclusion forcée (DDA/MEMO) à des fins d'exclusion du contenu.

*   La variable `is_architecture_doc = AnalysisProfile.is_always_included(path_for_filtering, path_components)` doit être calculée après l'écriture du fichier distinct (étape 6).
*   La création du `file_block` et l'ajout aux listes de consolidation doivent être conditionnels :

```python
if not is_architecture_doc: # Exclut DDA_V*.md et MEMO_TECH_V*.md
    # ... Création de file_block ...
    full_code_content_parts.append(file_block)
    # ... autres ajouts ...
    categorized_files.append((file_block, categories))
```

## 5. Risques et Compromis

| Risque | Description | Compromis Accepté |
| :--- | :--- | :--- |
| **Fuite Contextuelle** | Un fichier de code légitime commence accidentellement par `DDA_V` et est exclu de la consolidation (P_4). | **Faible**. La convention de nommage est suffisamment stricte. Le gain en pureté contextuelle (pour les LLMs) l'emporte sur le risque. |
| **Filtrage Excessif** | Un fichier minifié `script.min.js` légitime est utilisé et exclu (P_1). | **Accepté**. Les LLMs traitent mal le code minifié. Nous privilégions la source non-minifiée (`script.js`). |
| **Lisibilité de l'Arbre** | `__arborescence.txt` est très long (P_3). | **Accepté**. La taille de l'arborescence est un coût minime (quelques tokens) pour une valeur informative maximale (Stack technique, structure des dépendances). |

## 6. Handoff au Lead Tech

L'implémentation doit se concentrer sur les deux points de contrôle critiques du pipeline :

1.  **Centraliser le Gatekeeper dans `base.py` :** Créer la constante `CRITICAL_IGNORED_SUFFIXES` et l'intégrer dans `AnalysisProfile.is_always_ignored`.
2.  **Mettre à jour le Pipeline dans `app.py` :**
    *   Ajouter l'appel au Gatekeeper (`AnalysisProfile.is_always_ignored`) comme première condition de skip dans la boucle de fichiers.
    *   Mettre à jour la liste `extensions_to_keep` pour inclure `.md`.
    *   Implémenter la condition d'exclusion de contenu (P_4) en utilisant `AnalysisProfile.is_always_included` pour bloquer les DDA/MEMO de l'ajout aux listes de consolidation.

*L'architecture est maintenant stable et optimisée pour la qualité du contexte d'analyse IA.*