# codetotext_core/__init__.py
# [Version 1.0]

# Package racine du moteur de traitement CodeToText
# Ce package encapsule la logique métier pure, indépendante du framework Flask.
# Il est structuré en sous-modules pour une séparation claire des responsabilités :
# - profiles : Contient les stratégies d'analyse des projets (pattern Strategy)
# - processing : Logique de transformation et de consolidation des fichiers
# - utils : Fonctions utilitaires génériques (identification de langage, génération d'arborescence)