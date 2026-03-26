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

PDP_MODULES = pdp_stone,pdp_metal,pdp_labor,pdp_margin,pdp_product,pdp_frontend

SIS_MODULES = sis_party,sis_document,sis_frontend

export PYTHONPATH := $(abspath rubicon_addons):$(PYTHONPATH)

.PHONY: help reset_odoo_db init-data-modules update-data-modules update-pdp-modules \
        update-sis-modules upgrade deploy-demo logs-demo logs-prod \
        raw_to_data_all import_all import_csv import_pictures audit_counts create_diagram \
        stone-data stone-install stone-import stone-all backup-help


# --- General ---

help:
	@echo ""
	@echo "Rubicon Suite — available commands"
	@echo ""
	@echo "  Database"
	@echo "    make reset_odoo_db          Drop volumes and restart stack"
	@echo "    make init-data-modules      Install core data modules from scratch"
	@echo "    make update-data-modules    Update core data modules (pdp_*)"
	@echo "    make update-pdp-modules     Update all PDP modules including frontend"
	@echo "    make update-sis-modules     Update all SIS modules including frontend"
	@echo "    make upgrade                Update all modules (PDP + SIS)"
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
	@echo "    make import_pictures        Import product pictures"
	@echo "    make audit_counts           Print record counts to log"
	@echo ""
	@echo "  Stone pipeline"
	@echo "    make stone-data             Generate stone CSV from raw data"
	@echo "    make stone-install          Install pdp_stone module"
	@echo "    make stone-import           Import stone data"
	@echo "    make stone-all              Full stone pipeline"
	@echo ""


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

upgrade:
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

import_all:
	@mkdir -p $(LOG_DIR)
	@echo "→ DB=$(DB)  script=$(IMPORT_CSV_SCRIPT)"
	$(ODOO_SHELL) < $(IMPORT_CSV_SCRIPT) 2>&1 | tee $(LOG_DIR)/import_$(TIMESTAMP).log

import_csv:
	@WHAT=$(WHAT) $(ODOO_SHELL) < ops/import/import_csv.py

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

backup-help:
	@cat meta/doc/backup.md


