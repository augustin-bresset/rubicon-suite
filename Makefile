# Rubicon Suite — development and operations commands.

# --- Config ---
-include .env
export

DB_NAME         ?= rubicon
DB_HOST         ?= localhost
DB_PORT         ?= 5432
DB_USER         ?= rubicondev
DB_PASS         ?= rubicondev

IMPORT_CSV_SCRIPT   ?= ops/migration/import/import_csv.py
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

.PHONY: help shell recompute-alt-codes propose-notation reset_odoo_db init-data-modules update-data-modules update-pdp-modules \
        update-sis-modules upgrade deploy-demo logs-demo logs-prod \
        restore-reference-csvs raw_to_data_all import_all import_csv import_pictures import-pictures \
        raw-to-data-sis import-sis sis-all \
        restore-mssql export-pictures audit_counts create_diagram \
        stone-data stone-install stone-all backup backup-help \
        cleanup-none-all migrate-picture-scope cleanup-orphan-pictures \
        verify-picture-chain \
        test-db-init test-tours test-tours-fresh


# --- General ---

help:
	@echo ""
	@echo "Rubicon Suite — available commands"
	@echo ""
	@echo "  Database"
	@echo "    make shell < script.py      Run a Python script inside odoo shell (env available)"
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
	@echo "    make import_all             Run full CSV import (PDP)"
	@echo "    make import_csv WHAT=...    Import a specific CSV"
	@echo "    make raw-to-data-sis        Generate SIS CSVs from data/backup_sis/"
	@echo "    make import-sis             Import SIS parties + documents (needs RUBICON_ALLOW_SIS_WIPE=1, backs up first)"
	@echo "    make sis-all                Full SIS pipeline: CSVs, modules, import"
	@echo "    make restore-mssql          Restore the 3 legacy .bak files and export CSVs + pictures (ops/migration/README.md)"
	@echo "    make export-pictures        Extract photos/drawings from Pictures.bak → data/pictures/"
	@echo "    make import-pictures        Import data/pictures/ into Odoo (pdp.picture)"
	@echo "    make recompute-alt-codes    Refresh the derived alternative codes after mapping curation"
	@echo "    make propose-notation       Prefill the notation dictionaries with frequency-based proposals"
	@echo "    make audit_counts           Print record counts to log"
	@echo ""
	@echo "  Stone pipeline"
	@echo "    make stone-data             Generate stone CSV from raw data"
	@echo "    make stone-install          Install pdp_stone module"
	@echo "    make stone-all              Stone data: generate CSV and install pdp_stone"
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

shell:
	@$(ODOO_SHELL)

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
	docker compose -f docker-compose.prod.yml logs -f odoo


# --- Data pipeline ---

# The converters regenerate every CSV, including the reference data that is
# curated by hand and tracked in git (stone catalogue, metals, margins, ...).
# `restore-reference-csvs` puts the tracked versions back so only the
# business data (products, models, documents, parties) comes from the export.
# Rerun after curating the Emasur mappings/aliases: refreshes the derived
# alternative codes (products, history...); official codes are never touched.
recompute-alt-codes:
	@printf 'import pprint\npprint.pprint(env["emasur.converter"].action_recompute_all())\nenv.cr.commit()\n' | $(ODOO_SHELL)

propose-notation:
	@printf 'import pprint\npprint.pprint(env["rubicon.notation"].action_propose_codes())\nenv.cr.commit()\n' | $(ODOO_SHELL)

restore-reference-csvs:
	@git checkout -q -- $$(git ls-files 'rubicon_addons/*/data/*.csv') && \
	  echo "→ tracked reference CSVs restored from git (business CSVs kept)"

raw_to_data_all:
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_stone
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_metal
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_product
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_labor
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_margin
	$(MAKE) restore-reference-csvs

import_all: backup
	@mkdir -p $(LOG_DIR)
	@echo "→ DB=$(DB)  script=$(IMPORT_CSV_SCRIPT)"
	$(ODOO_SHELL) < $(IMPORT_CSV_SCRIPT) 2>&1 | tee $(LOG_DIR)/import_$(TIMESTAMP).log

import_csv:
	@WHAT=$(WHAT) $(ODOO_SHELL) < ops/migration/import/import_csv.py

# --- SIS data pipeline ---

raw-to-data-sis:
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_sis
	$(MAKE) restore-reference-csvs

# Deletes every sis.document before reloading: the importer refuses to run
# unless RUBICON_ALLOW_SIS_WIPE=1 is given explicitly on the make command line.
import-sis: backup
ifneq ($(RUBICON_ALLOW_SIS_WIPE),1)
	$(error import-sis wipes all SIS documents of DB=$(DB) — run: make import-sis RUBICON_ALLOW_SIS_WIPE=1)
endif
	@mkdir -p $(LOG_DIR)
	@echo "→ DB=$(DB)  parties → ops/migration/import/import_sis_parties.py"
	$(ODOO_SHELL) < ops/migration/import/import_sis_parties.py   2>&1 | tee $(LOG_DIR)/import_sis_parties_$(TIMESTAMP).log
	@echo "→ DB=$(DB)  documents → ops/migration/import/import_sis_documents.py"
	docker compose exec -T -e RUBICON_ALLOW_SIS_WIPE=1 odoo odoo shell \
	  --db_host=$(DB_HOST) --db_port=$(DB_PORT) \
	  --db_user=$(DB_USER) --db_password=$(DB_PASS) \
	  -d $(DB) --no-http < ops/migration/import/import_sis_documents.py 2>&1 | tee $(LOG_DIR)/import_sis_docs_$(TIMESTAMP).log

sis-all: raw-to-data-sis update-sis-modules import-sis

restore-mssql:
	./ops/migration/restore_mssql.sh all

export-pictures:
	./ops/migration/restore_mssql.sh pictures

import-pictures:
	$(ODOO_SHELL) < ops/migration/import/import_pictures.py

import_pictures:
	@$(ODOO_SHELL) < ops/migration/import/import_pictures.py

audit_counts:
	@mkdir -p $(LOG_DIR)
	@$(ODOO_SHELL) < ops/migration/audit/audit_counts.py | tee $(LOG_DIR)/counts_$(TIMESTAMP).log

create_diagram:
	@mkdir -p $(LOG_DIR)
	@$(ODOO_SHELL) < ${CREATE_DIAGRAM} | tee $(LOG_DIR)/diagram.log
	docker compose cp odoo:/var/lib/odoo/odoo_erd.puml ./odoo_erd.puml


# --- Stone pipeline ---

stone-data:
	$(PY) -m rubicon_import.raw_to_data.raw_to_data_stone

stone-install:
	$(ODOO) -i pdp_stone --without-demo=all --stop-after-init --workers=0

stone-all: stone-data stone-install

# --- Demo ---



# --- Misc ---

cleanup-none-all: backup
	$(ODOO_SHELL) < ops/migration/cleanup/cleanup_none_all.py

migrate-picture-scope:
	$(ODOO_SHELL) < ops/migration/cleanup/migrate_picture_scope.py

cleanup-orphan-pictures:
	$(ODOO_SHELL) < ops/migration/cleanup/cleanup_orphan_pictures.py

verify-picture-chain:
	$(ODOO_SHELL) < ops/migration/verify/verify_picture_chain.py

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


