## Roadmap Rubicon Suite

1. **Préparation de l’environnement**

   * Docker Compose : PostgreSQL 13 + Odoo 18
   * Montage de vos dossiers `odoo_conf/` et `rubicon_addons/`
   * Initialisation de la base `odoo` (module `base`) pour sortir de l’erreur 500

2. **Package métier léger (`rubicon_core`)**

   * Création d’un package Python séparé
   * SQLAlchemy + Alembic pour gérer le schéma `metier`
   * Modèles de base et première migration

3. **Conception du schéma de données**

   * Recensement des entités métier (produits, pierres, marges…)
   * Diagramme ER / PlantUML et définition du schéma `metier`
   * Ajustement des migrations Alembic

4. **Scaffolding du module Odoo (`rubicon_addons/pdp`)**

   * Création du dossier, `__manifest__.py` minimal, structure Python
   * Déclaration des modèles `models.Model` pointant sur le schéma `metier`
   * Configuration de `addons_path` et tests de chargement

5. **Gestion et migration de la base existante**

   * **Restaurer** votre backup SQL dans un schéma de test (ou base temporaire)
   * **Explorer** la structure : liste des tables, relations, volumes de données
   * **Mapper** les tables anciennes → nouveaux modèles (`rubicon_core`/Odoo)
   * **Écrire** des scripts de migration (ETL) : en Python/SQLAlchemy ou via psql
   * **Valider** sur un jeu réduit (tests d’intégrité, données critiques)

6. **Intégration et déploiement**

   * Charger les données migrées dans le schéma `metier` de votre base Odoo
   * Installer et tester le module PDP dans Odoo
   * Mettre en place un pipeline CI (tests Pytest, migrations Alembic, checks Odoo)

7. **Tests, documentation et formation**

   * Rédiger des tests unitaires pour la logique métier et des tests d’intégration Odoo
   * Documenter le processus de migration et d’installation
   * Former les utilisateurs à l’environnement Rubicon Suite
