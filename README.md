# Rubicon Suite

## Installation
###  Prerequisite

* Docker & Docker Compose
* Python 3.10+ 

### Setup

To set up the project on a new machine, you only need **Git** and **Docker (with Compose)**. Clone the repository, configure the `.env` file, and start the containers:

```bash
git clone <repository-url>
cd rubicon-suite
cp .env.example .env   # adjust database settings if needed
docker compose up -d
```

Before continuing you need to have extracted the data files in `data/raw/` as described in `meta/doc/backup.md`.


Once the containers are running, initialize the core modules and import data using the provided Makefile:

```bash
make init-data-modules
make raw_to_data_all
make import_all
```

This will install Odoo, set up the Rubicon core modules, and load all CSV datasets. The environment is fully reproducible across machines since all dependencies are encapsulated in Docker.

Optional
```bash
make audit_counts
make create_diagram
```
To be sure that everything is ok and to create a diagram of the database.

Finally you can connect to Odoo at `http://localhost:8069` and start using the Rubicon Suite.




### Configuration

1. Copy the example environment file:


```bash
cp .env.example .env
```

2. Edit `.env`:

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

3. Add `.env` to your `.gitignore` to avoid committing sensitive information.

---

## Quick Start

Launch PostgreSQL + Odoo :

```sh
docker compose up -d
```

* PostgreSQL `localhost:5432`
* Odoo `http://localhost:8069`


## Database


* Recreate the database
```sh
docker compose run --rm odoo   odoo     --db_host=db     --db_port=5432     --db_user=rubicondev     --db_password=passwd     -d rubicon -i base     --stop-after-init
```

* Dump de la base
```sh
docker compose exec db pg_dump -U rubicondev rubicon > dump.sql
```

* Restaurer la base
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

1. `Port 8069 is in use by another program.`

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

## Makefile

The provided **Makefile** defines a set of helper commands to manage the Odoo development environment and data pipeline. You can run `make <target>` for the following:

* `reset_odoo_db` – restart the Odoo Docker stack and reset volumes.
* `init-data-modules` – install the core Rubicon modules (`pdp_stone`, `pdp_metal`, `pdp_labor`, `pdp_margin`, `pdp_product`).
* `update-data-modules` – update the same modules without reinstalling.
* `raw_to_data_all` – run all raw-to-data transformations (stones, metals, products, labor, margins).
* `import_all` – import all CSVs into the database, with logs saved under `meta/logs/`.
* `import_csv` – import a specific dataset by passing `WHAT=<name>`.
* `audit_counts` – run consistency checks and produce a log of record counts.
* `create_diagram` – generate an ER diagram of the database schema (`odoo_erd.puml`).
* `stone-data` / `stone-install` / `stone-import` / `stone-all` – dedicated pipeline for stone data: transform raw data, install the `pdp_stone` module, and import records.

These shortcuts simplify repetitive tasks such as resetting the database, installing modules, importing data, auditing, or generating diagrams.


### Example usage

To reset the Odoo database and install all core data modules, you can run:

```sh
make reset_odoo_db
make init-data-modules
```

Run an audit on the project :

```sh
make audit_counts
make create_diagram
```


## ROADMAP

### What have been done

CRUD modules for :
* Stone
* Metal
* Product
* Labor
* Margin

Data Flow for those modules from CSV files

Price computation with pdp_price based on the data of the CRUD modules.

### What is next
* Frontend for PDP
* Files generation from html templates (pdf, docx, xlsx)
* SIS (Sales Information System) backend :
   * Orders
   * Customers
   * Invoices
* PCS (Production Control System) backend :
   * Dashboard containing
      * Stone production states (assorting, shaping, cutting)
      * Product production states (wax, casting, assembly, polishing, quality control, ...)
   * Priority List
   