# Rubicon Suite


## Prerequisite

* Docker & Docker Compose
* Python 3.10+ 

---


## Configuration

1. Copier le fichier d'exemple :

   ```sh
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

## Quick Start

Launch PostgreSQL + Odoo :

```sh
docker compose up -d
```

* PostgreSQL `localhost:5432`
* Odoo `http://localhost:8069`

---


## Installer un addon

1. Copier/monter `rubicon_addons` via `docker-compose` (voir `volumes`)
2. Redémarrer le service Odoo :

```sh

docker compose restart odoo

```

3. Connectez-vous à `http://localhost:8069`, et installez votre addon `pdp`.



## Database


Recreer les tables odoo

```sh
docker compose run --rm odoo   odoo     --db_host=db     --db_port=5432     --db_user=rubicondev     --db_password=passwd     -d rubicon -i base     --stop-after-init
```
Dump de la base

```sh
docker compose exec db pg_dump -U rubicondev rubicon > dump.sql
```

Restaurer la base

```sh
cat dump.sql | docker compose exec -T db psql -U rubicondev rubicon
```   

## Testing modules 

In each modules a **tests** folder will be found. It contains the tests.

You can launch those test by launching 
```sh
docker compose exec -T odoo \
  odoo -d rubicon \
  -u [INSERT_MODULE_NAME] \
  --stop-after-init \
  --test-enable
```

### Errors handling

1.Port 8069 is in use by another program.

It happens when odoo is already in use, you can add *--no-http* to the command before such as below 

```sh
docker compose exec -T odoo \
  odoo -d rubicon \
  -u [INSERT_MODULE_NAME] \
  --stop-after-init \
  --test-enable \
  --no-http
```

Or choosing an other port with *--http-port=xxx* such as below :
```sh
docker compose exec -T odoo \
  odoo -d rubicon \
  -u [INSERT_MODULE_NAME] \
  --stop-after-init \
  --test-enable \
  --http-port=8070
```


