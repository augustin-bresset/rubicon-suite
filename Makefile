# Create commands for the project.



# --- Config ---
-include .env
export

ODOO_BIN        ?= odoo
DB_NAME         ?= $(DB_NAME)
DB_HOST         ?= $(DB_HOST)
DB_PORT         ?= $(DB_PORT)
DB_USER         ?= $(DB_USER)
DB_PASS         ?= $(DB_PASS)

IMPORT_CSV_SCRIPT   ?= ops/import/import_csv.py
CREATE_DIAGRAM		?= rubicon_addons/rubicon_import/analysis/diagram.py

LOG_DIR         ?= meta/logs
TIMESTAMP       := $(shell date +%F_%H%M)

DB := $(if $(DB_NAME),$(DB_NAME),rubicon)	

ODOO = docker compose exec -T odoo $(ODOO_BIN) -d $(DB)
PY   := python3

ODOO_SHELL = docker compose exec -T odoo odoo shell \
  --db_host=$(DB_HOST) --db_port=$(DB_PORT) \
  --db_user=$(DB_USER) --db_password=$(DB_PASS) \
  -d $(DB) --no-http

CORE_DATA_MODULES = pdp_stone,pdp_metal,pdp_labor,pdp_margin,pdp_product

PDP_MODULES = pdp_stone,pdp_metal,pdp_labor,pdp_margin,pdp_product,pdp_frontend

SIS_MODULES = sis_party,sis_document,sis_frontend


export PYTHONPATH := $(abspath rubicon_addons):$(PYTHONPATH)

LOG_DIR ?= meta/logs
TIMESTAMP = $(SHELL date +%F_%H%M)



# --- General ---- 

help: cat README.md


reset_odoo_db:
	docker compose down -v
	docker compose up -d

init-data-modules:
	$(ODOO) -i rubicon_env,$(CORE_DATA_MODULES) --stop-after-init --workers=0

update-data-modules:
	$(ODOO) -u $(CORE_DATA_MODULES) --stop-after-init --workers=0

update-sis-modules:
	$(ODOO) -u $(CORE_DATA_MODULES) --stop-after-init --workers=0


raw_to_data_all:
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_stone
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_metal
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_product
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_labor
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_margin

import_all:
	@mkdir -p $(LOG_DIR)
	@echo "→ DB=$(DB)  script=$(IMPORT_CSV_SCRIPT)"
	$(ODOO_SHELL) < $(IMPORT_CSV_SCRIPT) 2>&1 | tee $(LOG_DIR)/import_$(TIMESTAMP).log



import_csv:
	@WHAT=$(WHAT) $(ODOO_SHELL) < ops/import/import_csv.py

import_pictures:
	@$(ODOO_SHELL) < ops/import/import_pictures.py


# ODOO_SHELL = docker compose exec -T odoo odoo shell -d $(DB_NAME) --no-http

audit_counts:
	@mkdir -p $(LOG_DIR)
	@$(ODOO_SHELL) < ops/audit/audit_counts.py | tee $(LOG_DIR)/counts_$(TIMESTAMP).log

create_diagram:
	@$(ODOO_SHELL) < ${CREATE_DIAGRAM} | tee $(LOG_DIR)/diagram.log
		@mkdir -p $(LOG_DIR)
	docker compose cp odoo:/var/lib/odoo/odoo_erd.puml ./odoo_erd.puml

# --- Pipeline STONE ---

.PHONY: stone-data stone-install stone-import stone-all db-reset

stone-data:
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_stone
stone-install:
	$(ODOO) odoo -d $(DB) -i pdp_stone --without-demo=all --stop-after-init --workers=0

stone-import:
	$(ODOO) odoo shell -d $(DB) < /mnt/extra-addons/rubicon-suite/scripts/stone_import.py

stone-import-standalone:
	$(ODOO) python3 /mnt/extra-addons/rubicon-suite/scripts/stone_import_standalone.py -d $(DB) -c /etc/odoo/odoo.conf

stone-all: stone-data stone-install stone-import

# --- Reset DB quand tu veux repartir de zéro ---
# db-reset:
# 	-$(PSQL) -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$(DB)';"
# 	-$(PSQL) -c "DROP DATABASE IF EXISTS $(DB);"
# 	$(PSQL) -c "CREATE DATABASE $(DB) ENCODING 'UTF8' TEMPLATE template0;"


# Restore Backup DB to CSV

backup-help:
	cat meta/doc/backup.md

