Voici une vue d’ensemble complète de la Rubicon Suite et de son architecture.

---

## 1. Objectif du projet

Rubicon Suite a pour but de remplacer et moderniser l’ensemble des outils PDP/SIS/RS/PSUtilities existants (basés sur MS SQL Server et applications compilées), en se reposant sur :

* **Odoo Community** pour la gestion ERP (ventes, stocks, facturation, utilisateurs, etc.)
* **Une couche métier indépendante** (rubicon\_core) codée en Python/SQLAlchemy pour encapsuler toute la logique de calcul de coûts (pierres, métaux, marges, devises…) et réutilisable hors d’Odoo
* **Des modules Odoo personnalisés** (rubicon\_addons) qui exposent dans Odoo les fonctionnalités métiers de rubicon\_core
* **Une isolation totale** des données de référence (pierres, métaux, pièces, taux de change…) et des données transactionnelles (commandes, lots, mouvements de stock), avec migrations de schéma gérées par Alembic

---

## 2. Architecture logicielle

```
rubicon-suite/
├─ data/            ← exemples de payloads JSON & CSV  
├─ meta/documents/  ← manuels et spécifications PDF  
├─ mssql_backups/   ← dumps .bak de l’ancien système  
├─ docker-compose.yml  
├─ odoo_conf/       ← config Odoo (odoo.conf, templates, etc.)  
├─ rubicon_addons/  ← modules Python/Odoo (18.0)  
└─ rubicon_core/    ← bibliothèque métier  
   ├─ db.py         ← engine SQLAlchemy & Session  
   ├─ requirements.txt  
   └─ models/       ← ORM models  
      ├─ reference/   ← tables “référence” (pierres, métaux, devises…)  
      └─ transaction/ ← tables transactionnelles (stock, ordres, lots…)  
```

1. **Monorepo**

   * Tout le code (module Odoo + couche métier + scripts + docs) dans un seul dépôt Git.
   * Permet de synchroniser versions et tests couvrant l’ensemble de la chaîne.
2. **Couche métier (rubicon\_core)**

   * **Python 3.12** (testé sous 3.12.x)
   * **SQLAlchemy 2.x** pour le mapping objet-relationnel
   * **Alembic 1.x** pour gérer les migrations de schéma
   * **psycopg2-binary 2.9.x** pour le driver PostgreSQL
   * Les modèles sont organisés en paquets `reference` et `transaction` afin de dissocier les données statiques des données évolutives
3. **Modules Odoo (rubicon\_addons)**

   * **Odoo Community 18.0**
   * Extensions Python qui importent rubicon\_core pour exposer menus, vues, rapports et API héritée
4. **Conteneurs Docker** orchestrés par **Docker Compose v2+**

   * **db** : `postgres:13` → base de données principale
   * **odoo** : `odoo:18.0` → application ERP
   * (éventuellement d’autres services—worker, reverse-proxy—selon la suite)

---

## 3. Gestion des variables d’environnement

* Fichier racine `.env` contenant :

  ```dotenv
  DB_HOST=db
  DB_PORT=5432
  DB_NAME=rubicon
  DB_USER=odoo
  DB_PASS=monpass
  ```
* `docker-compose.yml` référence ces variables pour initialiser Postgres et pour passer la chaîne `DATABASE_URL` à Alembic/SQLAlchemy et à Odoo.

---

## 4. Cycle de vie

1. **Installation locale**

   ```bash
   git clone … rubicon-suite
   cd rubicon-suite
   python3.12 -m venv .venv && source .venv/bin/activate
   pip install -r rubicon_core/requirements.txt
   ```
2. **Lancement des conteneurs**

   ```bash
   docker compose down  # détruit anciens conteneurs
   docker compose up -d  # démarre db & odoo
   ```
3. **Migrations de schéma**

   ```bash
   cd rubicon_core
   alembic upgrade head       # crée toutes les tables en PostgreSQL
   ```
4. **Démarrage Odoo**

   * Odoo lit `odoo_conf/odoo.conf` (interpolé via `.env` si besoin)
   * Les modules `rubicon_addons` sont automatiquement installés
5. **Utilisation**

   * Toute logique métier complexe (calcul de coût, conversion de devises…) passe par rubicon\_core,
   * Les utilisateurs interagissent via l’interface Odoo.

---

### En résumé

Rubicon Suite offre un **ERP moderne**, découplé en :

1. **Docker** pour l’isolation et la reproductibilité de l’environnement
2. **PostgreSQL** géré via conteneur + **migrations Alembic**
3. **SQLAlchemy/Alembic** pour versionner et évoluer le schéma de données
4. **Odoo 18** pour l’interface utilisateur et les workflows
5. **rubicon\_core** pour la couche métier pure Python
6. **rubicon\_addons** pour l’intégration Odoo

Cet empilement garantit une **maintenance simplifiée**, une **scalabilité modulable** et la **séparation claire** entre logique métier et interface.
