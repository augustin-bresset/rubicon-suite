# --- Config ---
SHELL := /bin/bash
.ONESHELL:
DB := rubicon
ODOO := docker compose exec -T odoo
PSQL := docker compose exec -T db psql -U odoo
PY   := python3

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
db-reset:
	-$(PSQL) -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$(DB)';"
	-$(PSQL) -c "DROP DATABASE IF EXISTS $(DB);"
	$(PSQL) -c "CREATE DATABASE $(DB) ENCODING 'UTF8' TEMPLATE template0;"
