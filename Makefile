# Rubicon Suite — development and operations commands.

# --- Config ---
-include .env
export

DB_NAME         ?= rubicon
DB_HOST         ?= localhost
DB_PORT         ?= 5432
DB_USER         ?= rubicondev
DB_PASS         ?= rubicondev

IMPORT_CSV_SCRIPT   ?= ops/import/import_csv.py
CREATE_DIAGRAM      ?= rubicon_addons/rubicon_import/analysis/diagram.py

LOG_DIR         ?= meta/logs
BACKUP_DIR      ?= meta/backups
BACKUP_LSN_FILE ?= $(BACKUP_DIR)/.last_lsn
TIMESTAMP       := $(shell date +%F_%H%M)

DB := $(if $(DB_NAME),$(DB_NAME),rubicon)

ODOO_BIN        ?= odoo
ODOO = docker compose exec -T odoo $(ODOO_BIN) -d $(DB)
PY   := python3

ODOO_SHELL = docker compose exec -T odoo odoo shell \
  --db_host=$(DB_HOST) --db_port=$(DB_PORT) \
  --db_user=$(DB_USER) --db_password=$(DB_PASS) \
  -d $(DB) --no-http

CORE_DATA_MODULES = pdp_stone,pdp_metal,pdp_labor,pdp_margin,pdp_product

PDP_MODULES = pdp_stone,pdp_metal,pdp_labor,pdp_margin,pdp_product,pdp_picture,pdp_frontend

SIS_MODULES = sis_party,sis_document,sis_frontend

export PYTHONPATH := $(abspath rubicon_addons):$(PYTHONPATH)

TEST_DB          ?= rubicon_test
ODOO_TEST        = docker compose exec -T odoo odoo \
  --db_host=$(DB_HOST) --db_port=$(DB_PORT) \
  --db_user=$(DB_USER) --db_password=$(DB_PASS) \
  -d $(TEST_DB)
TEST_TAGS        ?= pdp_frontend

.PHONY: help reset_odoo_db init-data-modules update-data-modules update-pdp-modules \
        update-sis-modules upgrade deploy-demo logs-demo logs-prod \
        raw_to_data_all import_all import_csv import_pictures import-pictures \
        export-pictures audit_counts create_diagram \
        stone-data stone-install stone-import stone-all backup backup-help \
        cleanup-none-all migrate-picture-scope \
        test-db-init test-tours test-tours-fresh


# --- General ---

help:
	@echo ""
	@echo "Rubicon Suite — available commands"
	@echo ""
	@echo "  Database"
	@echo "    make reset_odoo_db          Drop volumes and restart stack"
	@echo "    make backup                 pg_dump rubicon → meta/backups/"
	@echo "    make init-data-modules      Install core data modules from scratch"
	@echo "    make update-data-modules    Update core data modules (pdp_*)"
	@echo "    make update-pdp-modules     Update all PDP modules including frontend"
	@echo "    make update-sis-modules     Update all SIS modules including frontend"
	@echo "    make upgrade                Update all modules (PDP + SIS) — runs backup first"
	@echo "    make update MODULE=name     Update a specific module"
	@echo ""
	@echo "  Deploy"
	@echo "    make deploy-demo            Pull latest code and restart demo stack"
	@echo "    make logs-demo              Follow demo Odoo logs"
	@echo "    make logs-prod              Follow production Odoo logs"
	@echo ""
	@echo "  Import"
	@echo "    make import_all             Run full CSV import"
	@echo "    make import_csv WHAT=...    Import a specific CSV"
	@echo "    make export-pictures        Extract photos/drawings from Pictures.bak → data/pictures/"
	@echo "    make import-pictures        Import data/pictures/ into Odoo (pdp.picture)"
	@echo "    make audit_counts           Print record counts to log"
	@echo ""
	@echo "  Stone pipeline"
	@echo "    make stone-data             Generate stone CSV from raw data"
	@echo "    make stone-install          Install pdp_stone module"
	@echo "    make stone-import           Import stone data"
	@echo "    make stone-all              Full stone pipeline"
	@echo ""


backup:
	@mkdir -p $(BACKUP_DIR)
	@CURRENT_LSN=$$(docker compose exec -T db psql -U $(DB_USER) $(DB_NAME) -Atc \
	  "SELECT pg_current_wal_lsn();") && \
	LAST_LSN=$$(cat $(BACKUP_LSN_FILE) 2>/dev/null || echo "") && \
	if [ "$$CURRENT_LSN" = "$$LAST_LSN" ]; then \
	  echo "→ No changes since last backup (LSN=$$CURRENT_LSN) — skipping."; \
	else \
	  OUTFILE=$(BACKUP_DIR)/$(DB_NAME)_$(TIMESTAMP).sql && \
	  echo "→ Dumping $(DB_NAME) → $$OUTFILE" && \
	  docker compose exec -T db pg_dump -U $(DB_USER) $(DB_NAME) > $$OUTFILE && \
	  echo "$$CURRENT_LSN" > $(BACKUP_LSN_FILE) && \
	  find $(BACKUP_DIR) -name "*.sql" -mtime +30 -delete && \
	  echo "→ Backup done: $$OUTFILE"; \
	fi

reset_odoo_db:
	docker compose down -v
	docker compose up -d

init-data-modules:
	$(ODOO) -i rubicon_env,$(CORE_DATA_MODULES) --stop-after-init --workers=0

update-data-modules:
	$(ODOO) -u $(CORE_DATA_MODULES) --stop-after-init --workers=0

update-pdp-modules:
	$(ODOO) -u $(PDP_MODULES) --stop-after-init --workers=0

update-sis-modules:
	$(ODOO) -u $(SIS_MODULES) --stop-after-init --workers=0

upgrade: backup
	$(ODOO) -u $(PDP_MODULES),$(SIS_MODULES) --stop-after-init --workers=0

update:
ifndef MODULE
	$(error MODULE is required — usage: make update MODULE=pdp_frontend)
endif
	$(ODOO) -u $(MODULE) --stop-after-init --workers=0

# --- Deploy ---

deploy-demo:
	git pull
	$(MAKE) update-pdp-modules
	$(MAKE) update-sis-modules
	docker compose -f docker-compose.demo.yml restart odoo_demo

logs-demo:
	docker compose -f docker-compose.demo.yml logs -f odoo_demo

logs-prod:
	docker compose logs -f odoo


# --- Data pipeline ---

raw_to_data_all:
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_stone
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_metal
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_product
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_labor
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_margin

import_all: backup
	@mkdir -p $(LOG_DIR)
	@echo "→ DB=$(DB)  script=$(IMPORT_CSV_SCRIPT)"
	$(ODOO_SHELL) < $(IMPORT_CSV_SCRIPT) 2>&1 | tee $(LOG_DIR)/import_$(TIMESTAMP).log

import_csv:
	@WHAT=$(WHAT) $(ODOO_SHELL) < ops/import/import_csv.py

export-pictures:
	@echo "→ Starting temporary SQL Server container…"
	docker run -d --name sqlsrv_pics --rm \
	  -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=Strong@Passw0rd" \
	  -p 1433:1433 \
	  -v $(abspath mssql_backups):/var/opt/mssql/backup \
	  mcr.microsoft.com/mssql/server:2019-latest
	@echo "→ Waiting for SQL Server to be ready…"
	sleep 20
	@echo "→ Restoring Pictures.bak…"
	docker exec sqlsrv_pics /opt/mssql-tools18/bin/sqlcmd \
	  -S localhost -U SA -P 'Strong@Passw0rd' -C \
	  -Q "RESTORE DATABASE PICTURES \
	      FROM DISK = '/var/opt/mssql/backup/Pictures.bak' \
	      WITH MOVE 'Pictures_Data' TO '/var/opt/mssql/data/Pictures.mdf', \
	           MOVE 'Pictures_Log'  TO '/var/opt/mssql/data/Pictures_log.ldf', \
	      REPLACE;"
	@echo "→ Exporting photos and drawings to data/pictures/ …"
	docker run --rm --network=host \
	  -v $(abspath .):/app \
	  -e PICTURES_OUT_DIR=/app/data/pictures \
	  python:3.11-slim bash -c " \
	    apt-get update -qq && apt-get install -y -qq unixodbc unixodbc-dev freetds-dev tdsodbc gcc > /dev/null 2>&1; \
	    pip install -q pyodbc tqdm; \
	    cd /app && python3 ops/export/export_pictures_products.py"
	docker stop sqlsrv_pics || true
	@echo "→ Done. Run 'make import-pictures' to import into Odoo."

import-pictures:
	$(ODOO_SHELL) < ops/import/import_pictures.py

import_pictures:
	@$(ODOO_SHELL) < ops/import/import_pictures.py

audit_counts:
	@mkdir -p $(LOG_DIR)
	@$(ODOO_SHELL) < ops/audit/audit_counts.py | tee $(LOG_DIR)/counts_$(TIMESTAMP).log

create_diagram:
	@mkdir -p $(LOG_DIR)
	@$(ODOO_SHELL) < ${CREATE_DIAGRAM} | tee $(LOG_DIR)/diagram.log
	docker compose cp odoo:/var/lib/odoo/odoo_erd.puml ./odoo_erd.puml


# --- Stone pipeline ---

stone-data:
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_stone

stone-install:
	$(ODOO) -i pdp_stone --without-demo=all --stop-after-init --workers=0

stone-import:
	$(ODOO_SHELL) < ops/import/stone_import.py

stone-all: stone-data stone-install stone-import

# --- Demo ---



# --- Misc ---

cleanup-none-all: backup
	$(ODOO_SHELL) < ops/cleanup/cleanup_none_all.py

migrate-picture-scope:
	$(ODOO_SHELL) < ops/cleanup/migrate_picture_scope.py

backup-help:
	@cat meta/doc/backup.md


# --- Tours / Tests ---

test-db-init:
	@echo "→ Dropping test DB $(TEST_DB) (if exists)…"
	docker compose exec -T db psql -U $(DB_USER) -d postgres \
	  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$(TEST_DB)';" \
	  -c "DROP DATABASE IF EXISTS $(TEST_DB);"
	@echo "→ Installing modules into $(TEST_DB)…"
	$(ODOO_TEST) -i rubicon_env,$(PDP_MODULES) --without-demo=all --stop-after-init --workers=0

test-tours:
	$(ODOO_TEST) -u pdp_frontend \
	  --test-enable --stop-after-init --workers=0 \
	  --http-port=8072 \
	  --db-filter=rubicon_test \
	  --test-tags $(TEST_TAGS)

test-tours-fresh: test-db-init test-tours


