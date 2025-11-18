**Document de Décision d'Architecture (DDA) : Refactorisation du Moteur Monolithique**

En tant qu'Architecte Logiciel et CTO, j'ai analysé la nécessité de refactoriser les fichiers monolithiques `app.py` et `analysis_profiles.py` afin de réduire la dette technique et de préparer le projet à l'ajout de nouvelles fonctionnalités.

---

## 1. Rappel des Exigences Fonctionnelles Structurantes (Objectifs de la Refactorisation)

Les décisions de cette refactorisation sont prises pour atteindre les objectifs structurants suivants :

1.  **Séparation des Préoccupations (SoC)** : Isoler la logique métier pure (filtrage, traitement de fichiers, génération de blocs de code) du *serveur* et de la couche d'interface utilisateur (Flask, routes, I/O HTTP).
2.  **Testabilité Unitaire** : Permettre de tester l'intégralité du moteur de traitement de ZIP et de la logique de profilage (Strategy Pattern) sans avoir à instancier un environnement Flask ou un serveur HTTP.
3.  **Réduction de la Dette Technique** : Diminuer la taille et la complexité cyclomatique des fichiers critiques (`app.py`, `analysis_profiles.py`).
4.  **Extensibilité Stratégique** : Simplifier l'ajout de nouveaux profils d'analyse ou de nouveaux utilitaires de traitement de fichiers.

## 2. Architecture Globale Proposée : Décomposition en Package Core

L'architecture va évoluer d'un Monolithe de Fichiers (un seul fichier par responsabilité majeure) à un **Monolithe Modulaire** basé sur un package Python central.

| Couche Actuelle | Module Cible (Responsabilité) | Fichiers Cibles (Structure) |
| :--- | :--- | :--- |
| **Serveur/I.O.** (`app.py`) | **Application (API/Web)** : Gestion des routes, requêtes HTTP, et I/O de haut niveau. | `server.py` (ou `app.py` réduit) |
| **Logique Métier** (`app.py`) | **Core/Processing** : Logique de traitement ZIP, lecture de flux d'octets, détection de langage, renommage. | `codetotext_core/processing/zip_processor.py` |
| **Profiles** (`analysis_profiles.py`) | **Core/Profiles** : Implémentation du Strategy Pattern (Abstrait + Concrets). | `codetotext_core/profiles/` (Package) |
| **Utilitaires** (`app.py`) | **Core/Utils** : Fonctions génériques non liées à la logique Profile (ex: Arborescence, Langage). | `codetotext_core/utils/file_utils.py` |

### Nouvelle Arborescence Cible

```
CodeToText-main
├── codetotext_core/
│   ├── __init__.py
│   ├── processing/
│   │   ├── __init__.py
│   │   └── zip_processor.py      <-- La fonction _process_zip_file refactorisée
│   ├── profiles/
│   │   ├── __init__.py           <-- Registre des PROFILES et Factory
│   │   ├── base.py               <-- Classe AnalysisProfile Abstraite
│   │   ├── complete_profile.py   <-- Classe CompleteProfile
│   │   └── ...                   <-- Chaque profil (AdminScolaire, ScenarioBuilder, etc.) dans son propre fichier.
│   └── utils/
│       ├── __init__.py
│       └── file_utils.py         <-- Fonctions get_language_from_filename, generate_zip_tree
├── app.py                      <-- Le nouveau point d'entrée minimaliste Flask
├── templates/
└── ... (autres fichiers de config)
```

## 3. Choix de la Stack Technologique et Justifications

La refactorisation est purement structurelle et n'introduit pas de nouvelle dépendance majeure.

### 3.a. Stack Principale

| Composant | Technologie | Justification |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+, Flask | Aucune raison de changer le socle technologique qui répond au besoin fonctionnel. |
| **Structure** | Packages et Modules Python | Utilisation de la modularité native de Python pour l'encapsulation et l'organisation. |
| **Gestion de la Logique** | Classes / Méthodes Statiques/d'Instance | La logique de traitement sera encapsulée dans une classe `ZipProcessor` pour mieux gérer les états intermédiaires de traitement. |

### 3.b. Dépendances Critiques et Versions Cibles

*   **SDK Google AI :** (Règle maintenue pour toute intégration future)
    *   **Décision :** Le projet utilisera **exclusivement** le SDK `google-genai`.
    *   **Patron d'API Obligatoire :** Toute interaction doit passer par un objet `client = genai.Client()` et utiliser la méthode `client.models.generate_content()` avec un paramètre `config=types.GenerateContentConfig(...)` pour passer la configuration. L'utilisation de `genai.GenerativeModel()` est formellement interdite.

## 4. Principes de Conception et Conventions Initiales

| Principe | Convention/Implémentation | Justification |
| :--- | :--- | :--- |
| **Isolation de la Logique Core** | **`app.py`** ne doit contenir que la logique d'initialisation Flask, les routes HTTP (`@app.route`) et la gestion des flux (I/O). Il appellera la logique métier via `ZipProcessor`. | Réduit la complexité de l'application web et facilite l'évolution. |
| **Encapsulation du Traitement** | Création de la classe `ZipProcessor` dans `processing/zip_processor.py`. Cette classe aura une méthode principale, par exemple `process_archive(self, input_stream: io.BytesIO, profile: AnalysisProfile, keep_ext: bool) -> io.BytesIO`. | L'état du traitement (compteur de fichiers, détection du préfixe commun) est mieux géré par une classe plutôt qu'une fonction monolithique. |
| **Clarté du Strategy Pattern** | Chaque profil d'analyse (ex: `CompleteProfile`) sera déplacé dans son propre fichier Python dans `codetotext_core/profiles/`. | Améliore l'onboarding. Un développeur sait immédiatement où chercher pour modifier ou ajouter un profil. |
| **Registre Centralisé** | La variable `PROFILES` (le dictionnaire de toutes les stratégies disponibles) doit être déclarée et exportée depuis `codetotext_core/profiles/__init__.py`. | Fournit un point d'accès unique au registre des profils, découplant le registre des implémentations de profil. |
| **I/O en Flux** | Toutes les fonctions de traitement de fichiers (ex: `ZipProcessor.process_archive`) doivent accepter et retourner des objets `io.BytesIO`. | Garantit que l'application reste **stateless** et qu'aucune écriture intermédiaire sur le disque n'est nécessaire pour le traitement. |

## 5. Conséquences des Choix et Points de Vigilance

| Conséquence / Compromis | Description |
| :--- | :--- |
| **Augmentation du nombre de fichiers** | Le nombre total de fichiers Python augmentera (environ 1 fichier par profil). **Compromis Accepté** : C'est le prix de l'organisation. |
| **Complexité des Imports** | Les chemins d'importation deviendront plus longs (ex: `from codetotext_core.processing.zip_processor import ZipProcessor`). **Point de Vigilance** : Utiliser des imports absolus pour la clarté et éviter les pièges des imports relatifs. |
| **Risque de Régression** | Le déplacement et la refonte des fonctions (en méthodes de classes) sont à haut risque si les tests unitaires ne sont pas mis en place. **Mesure d'Atténuation** : La première étape de la refactorisation doit être d'entourer la logique de `_process_zip_file` (avant refonte) d'un jeu de tests d'intégration robuste (test en boîte noire, input ZIP -> output ZIP). |
| **Couplage du Registre** | `codetotext_core/profiles/__init__.py` restera le seul point de couplage fort, car il doit importer tous les profils concrets pour construire le dictionnaire `PROFILES`. Ce couplage est nécessaire et acceptable pour l'implémentation du Strategy Pattern. |

## 6. Prochaines Étapes et Handoff au Prompteur

Une fois ce Document de Décision d'Architecture validé, vous pouvez transmettre l'intégralité de ce DDA, ainsi que la Spécification Fonctionnelle originale et les clarifications apportées, à notre Chef de Développement (le Prompteur).

Son rôle sera alors de :
1.  Prendre en compte cette architecture comme la nouvelle structure cible du projet.
2.  Découper cette refactorisation en tâches de développement concrètes et ordonnées (ex: 1. Créer la structure de dossiers. 2. Déplacer `AnalysisProfile` vers `base.py`. 3. Refactoriser `_process_zip_file` en `ZipProcessor.process_archive`).
3.  Générer les prompts nécessaires pour le Codeur Sénior afin de mettre en œuvre cette nouvelle architecture modulaire.

Votre mission pour la structuration de ce projet est terminée.