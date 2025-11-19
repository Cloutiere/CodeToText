**Document de Décision d'Architecture (DDA) : Amélioration du Moteur de Filtrage CodeToText**

En tant qu'Architecte Logiciel et CTO, j'ai analysé la Spécification Fonctionnelle concernant l'amélioration des profils de filtrage et des règles de conservation d'extension de l'application CodeToText.

Cette initiative, bien que ciblée sur des détails d'implémentation, est structurante car elle modifie les règles fondamentales de traitement du code source, impactant directement la qualité des livrables d'analyse.

---

## 1. Rappel des Exigences Fonctionnelles Structurantes

Les décisions d'architecture et d'implémentation sont prises pour satisfaire les exigences clés suivantes :

1.  **Exhaustivité Contextuelle (AC-1)** : Le profil d'analyse `CompleteProfile` doit inclure les répertoires `tests/` et `.github/` afin de fournir une vue exhaustive des stratégies de test et de CI/CD.
2.  **Configuration Critique (AC-2)** : Le fichier `.replit` doit être considéré comme une configuration critique et inclus de manière systématique par tous les profils.
3.  **Préservation du Code Source Primaire (AC-3)** : L'extension `.py` doit être systématiquement conservée dans l'archive de sortie pour garantir une identification aisée des fichiers de code source principaux.

## 2. Architecture Globale Proposée

L'architecture existante de type **Monolithe Flask** est conservée. Le principe de conception **Stratégie (Strategy Pattern)**, implémenté via la classe abstraite `AnalysisProfile`, reste la fondation de la logique de filtrage et de catégorisation.

Les modifications requises sont chirurgicales et se concentrent sur :
*   L'ajustement des règles d'exclusion dans les classes concrètes de `AnalysisProfile`.
*   La modification de la liste blanche d'extensions à conserver dans la fonction de traitement `_process_zip_file` de `app.py`.

## 3. Choix de la Stack Technologique et Justifications

L'initiative ne nécessite pas de changement de stack. Les choix existants sont reconfirmés pour le développement à venir.

### 3.a. Stack Principale

| Composant | Technologie | Justification |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+, Flask | Framework léger et performant, adapté à une application utilitaire sans état (stateless). |
| **Logique de Filtrage** | Strategy Pattern (`AnalysisProfile`) | Permet une grande flexibilité et maintenabilité pour ajouter de nouveaux profils d'analyse sans impacter le cœur de l'application. |
| **Base de Données** | Aucune (Stateless) | Confirme la nature transactionnelle (entrée/sortie) de l'outil. |

### 3.b. Dépendances Critiques et Versions Cibles

*   **SDK Google AI :**
    *   **Contexte Critique :** La base de connaissances des LLMs de développement est antérieure à la sortie du SDK unifié `google-genai` (2025). Par conséquent, ils ont une forte tendance à régresser en utilisant des patrons de l'ancien SDK (`google-generativeai`), comme `genai.GenerativeModel()`, ce qui cause des `AttributeError`. Cette règle est un garde-fou non-négociable contre cette limitation.
    *   **Décision :** Le projet utilisera **exclusivement** le SDK `google-genai`.
    *   **Patron d'API Obligatoire :** Toute interaction doit passer par un objet `client = genai.Client()` et utiliser la méthode `client.models.generate_content()` avec un paramètre `config=types.GenerateContentConfig(...)` pour passer la configuration. L'utilisation de `genai.GenerativeModel()` est formellement interdite.
    *   **Sources de Vérité :** En cas de doute, la seule référence valide est la documentation officielle : `https://googleapis.github.io/python-genai/` et le guide de migration `https://ai.google.dev/gemini-api/docs/migrate-from-gendev`.

## 4. Principes de Conception et Conventions Initiales

Les conventions suivantes guideront l'implémentation des changements :

| Principe | Implémentation Ciblée | Justification |
| :--- | :--- | :--- |
| **Exclusion Granulaire (AC-1)** | Modification de `CompleteProfile.IGNORED_DIRS_OR_COMPONENTS` dans `analysis_profiles.py`. Les composants **`.github`** et **`tests`** sont retirés de la liste des répertoires ignorés. | Permet au profil le plus exhaustif d'inclure les stratégies de CI/CD et les cas de test, essentiels à l'analyse contextuelle. |
| **Gestion des Critiques (AC-2)** | Suppression de l'exclusion spécifique de `.replit` dans `CodeToTextProfile.is_file_ignored` et confirmation de son inclusion dans `AnalysisProfile.CRITICAL_CONFIG_BASENAMES`. | Uniformise le traitement de `.replit` comme un fichier de configuration critique, le rendant visible dans tous les profils sans exception, ce qui est crucial pour le contexte d'exécution. |
| **Liste Blanche d'Extensions (AC-3)** | Ajout de **`.py`** à la liste `extensions_to_keep` dans la fonction `_process_zip_file` de `app.py`. | Assure que les fichiers Python conservent leur extension d'origine même si l'option "Conserver l'extension d'origine" est désactivée. Cette liste blanche est considérée comme un minimum vital pour la lisibilité du code source. |

## 5. Conséquences des Choix et Points de Vigilance

| Conséquence / Compromis | Description |
| :--- | :--- |
| **Augmentation de la charge d'analyse** | L'inclusion de `tests/` et `.github/` dans le `CompleteProfile` (AC-1) augmentera le nombre total de fichiers à traiter et la taille de l'archive de sortie. **Compromis Accepté** : C'est le but recherché pour un profil "Complet". |
| **Cohérence des Noms de Fichiers** | L'ajout de `.py` à la liste blanche (AC-3) clarifie le nommage pour les fichiers Python, mais la logique de renommage en `.txt` pour les autres extensions doit être maintenue sans erreur. **Point de Vigilance** : Le développeur doit s'assurer que la condition de renommage est correctement appliquée : `if keep_original_extension or ext in extensions_to_keep or ...` doit fonctionner comme un *court-circuit* de non-renommage. |
| **Transparence du `.replit`** | Le fichier `.replit` sera toujours inclus (AC-2). **Conséquence** : L'Analyste aura systématiquement accès aux instructions d'exécution de Replit, ce qui est très bénéfique pour la reproductibilité. |

## 6. Prochaines Étapes et Handoff au Prompteur

Une fois ce Document de Décision d'Architecture validé, vous pouvez transmettre l'intégralité de ce DDA, ainsi que la Spécification Fonctionnelle originale et les clarifications apportées, à notre Chef de Développement (le Prompteur).
Son rôle sera alors de :
1. Prendre en compte cette architecture comme la base technique du projet.
2. Découper la Spécification Fonctionnelle initiale en tâches de développement concrètes et ordonnées (incluant les modifications spécifiques dans `analysis_profiles.py` et `app.py`).
3. Générer les prompts nécessaires pour le DBA Stratégique et le Codeur Sénior afin de mettre en œuvre cette architecture et les premières fonctionnalités.
Votre mission pour la genèse de ce projet est terminée.