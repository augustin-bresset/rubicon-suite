# Rubicon Suite

Ce dépôt contient l’ensemble des composants pour **Rubicon**, l’outil de gestion de production de bijoux : la configuration Odoo, les modules Odoo personnalisés (`rubicon_addons`), ainsi que la couche métier indépendante (`rubicon_core`).

---

## 📁 Structure du projet

```bash
rubicon-suite/
├── .env                   # Variables d'environnement (non versionné)
├── docker-compose.yml     # Orchestration Docker (PostgreSQL + Odoo)
├── data/
│   └── examples/          # Jeux de données d'exemple (JSON, CSV)
├── odoo_conf/             # Config Odoo (optionnel)
│   └── odoo.conf
├── rubicon_addons/        # Addons Odoo personnalisés
│   └── pdp/
├── rubicon_core/          # Couche métier SQLAlchemy
│   ├── db.py
│   └── models/
├── alembic/               # Répertoire des migrations Alembic
├── README.md              # Ce fichier
└── .gitignore
```

---

## ⚙️ Prérequis

* Docker & Docker Compose
* Python 3.10+ (localement si vous exécutez les migrations hors Docker)
* `pip install alembic python-dotenv psycopg2-binary`

---

## 🔒 Configuration

1. Copier le fichier d'exemple :

   ```bash
   cp .env.example .env
   ```

2. Éditer `.env` pour définir :

   ```ini
   # Base de données
   DB_HOST=db
   DB_PORT=5432
   DB_NAME=rubicon
   DB_USER=rubicon
   DB_PASS=un_mot_de_passe

   # URL SQLAlchemy / Alembic
   DATABASE_URL=postgresql+psycopg2://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
   ```

3. Ajouter `.env` à `.gitignore` pour éviter de versionner vos secrets.

---

## 🚀 Démarrage rapide (Docker)

Lancer PostgreSQL + Odoo :

```bash
docker compose up -d
```

* PostgreSQL écoute sur `localhost:5432`
* Odoo disponible sur `http://localhost:8069`

---

## 🛠️ Migrations de la base (Alembic)

> **Note :** exécuter depuis le conteneur ou local avec `.env`

### a) Initialisation (une seule fois)

```bash
cd rubicon_core
alembic init alembic
```

### b) Génération et application

```bash
# Création d'une révision (modèles SQLAlchemy déjà chargés)
alembic revision --autogenerate -m "Initial models"

# Appliquer la migration
alembic upgrade head
```

Pour exécuter dans le conteneur Docker `web` (si configuré) :

```bash
docker-compose run --rm web alembic upgrade head
```

---

## 📦 Exécution d’Odoo avec vos modules

1. Copier/monter `rubicon_addons` via `docker-compose` (voir `volumes`)
2. Redémarrer le service Odoo :

```bash

docker compose restart odoo

```

3. Connectez-vous à `http://localhost:8069`, et installez votre addon `pdp`.
```


## Database


Recreer les tables odoo

```
docker compose run --rm odoo   odoo     --db_host=db     --db_port=5432     --db_user=rubicondev     --db_password=passwd     -d rubicon -i base     --stop-after-init
```
