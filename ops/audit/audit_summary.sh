#!/usr/bin/env bash
set -euo pipefail

DCX="docker compose exec -T"
ODOO="$DCX odoo"
DB="$DCX db"
DBUSER="${DBUSER:-rubicondev}"
DBNAME="${DBNAME:-rubicon}"

# Sélecteur grep: préfère rg, sinon grep -P, puis grep -E
if command -v rg >/dev/null 2>&1; then
  echo "[info] using ripgrep (rg)"
  RG() { rg -n "$1" "${@:2}"; }
elif grep -P "" </dev/null >/dev/null 2>&1; then
  echo "[info] using grep -P"
  RG() { grep -R -nP "$1" "${@:2}"; }
else
  echo "[info] using grep -E"
  RG() { grep -R -nE "$1" "${@:2}"; }
fi

banner(){ printf "\n=== %s %s ===\n" "$1" "$(printf '%.0s=' {1..46})"; }

banner "ENVIRONNEMENT ODOO"
docker compose exec odoo odoo --version
$ODOO python3 - <<'PY'
import odoo
from odoo.tools import config
print("addons_path:", config['addons_path'])
PY

banner "MODULES LOCAUX (manifest -> name,version,depends,data counts)"
python3 - <<'PY'
import ast,glob,os
def load_manifest(p):
    src=open(p,'r',encoding='utf-8').read()
    tree=ast.parse(src, filename=p, mode='exec')
    d=None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(getattr(t,'id','')=='__manifest__' for t in n.targets):
            d=ast.literal_eval(n.value); break
    if not isinstance(d, dict): return None
    return {
        'path': p,
        'name': d.get('name'),
        'version': d.get('version'),
        'depends': d.get('depends', []),
        'data_len': len(d.get('data', [])),
        'demo_len': len(d.get('demo', [])),
    }
mods = sorted(glob.glob('rubicon_addons/*/__manifest__.py'))
for p in mods:
    m=load_manifest(p)
    if m:
        print(f"- {os.path.dirname(p)} :: {m['name']} v{m['version']} | depends={m['depends']} | data={m['data_len']} demo={m['demo_len']}")
PY

banner "ERD ODOO (puml présent ?)"
if [ -f odoo_erd.puml ]; then
  echo "odoo_erd.puml: OK (tail -n 5):"; tail -n 5 odoo_erd.puml
else
  echo "odoo_erd.puml: ABSENT"
fi

banner "MODELES (déclarés dans le code)"
# ERE: _name[spaces]*=[spaces]*'pdp.xxx'
RG "_name[[:space:]]*=[[:space:]]*'pdp\.[^']+'" rubicon_addons 2>/dev/null | sed 's/:.*_name/\t_name/' | sort -u || true

banner "CHAMPS MONETAIRES (usage 'currency_id' vs 'currency')"
# Recherche les champs Monetary + usages currency_id / 'currency ='
RG "Monetary|currency_id[[:space:]]*=|(^|[^A-Za-z_])currency[[:space:]]*=" rubicon_addons 2>/dev/null | sed 's/^/  /' | head -n 80 || true

banner "VUES & MENUS (Odoo 18 => <list> au lieu de <tree>)"
RG "<(form|list|kanban|search|tree|menuitem|act_window)" rubicon_addons 2>/dev/null | sed 's/^/  /' | head -n 120 || true

banner "PRICING (wizards & logique) — signatures compute/_convert/round"
# Escapes OK pour -E/-P; le round\( est littéral
RG "class[[:space:]]+pdp\.price|class[[:space:]]+Price|def[[:space:]]+compute|def[[:space:]]+_convert|round\(|@api\.depends" rubicon_addons/pdp_price 2>/dev/null | sed 's/^/  /' || true

banner "PIPELINE D'IMPORT (structure rapide)"
echo "[modules]"
ls -1 rubicon_addons/rubicon_import/raw_to_data/*.py 2>/dev/null | sed 's/^/  /' || true
echo "[fonctions clés]"
RG "def[[:space:]]+(build_|map_|transform_|run)" rubicon_addons/rubicon_import 2>/dev/null | sed 's/^/  /' | head -n 120 || true
echo "[entêtes CSV transformés (data/*.csv)]"
shopt -s nullglob
csv_files=(rubicon_addons/pdp_*/data/*.csv)
for f in "${csv_files[@]}"; do
  echo "  - $(basename "$f"): $(head -n1 "$f" | cut -c1-200)"
done
shopt -u nullglob

banner "DEVISES/RATES (fixtures & env)"
echo "[hooks]"
RG "currency|rate|_convert|res_currency" rubicon_addons/rubicon_env 2>/dev/null | sed 's/^/  /' || true
echo "[res_currency.xml (5 premières lignes utiles)]"
sed -n '1,80p' rubicon_addons/rubicon_env/data/res_currency.xml 2>/dev/null | sed 's/^/  /' | head -n 40 || true

banner "MENUS/ACTIONS/SECURITE"
echo "[menus]"
RG "<menuitem" rubicon_addons 2>/dev/null | sed 's/^/  /' | head -n 80 || true
echo "[actions]"
RG "<act_window" rubicon_addons 2>/dev/null | sed 's/^/  /' | head -n 80 || true
echo "[droits accès]"
for f in rubicon_addons/*/security/ir.model.access.csv; do
  echo "  - $f"; (head -n1 "$f"; tail -n +2 "$f" | head -n 10) | sed 's/^/     /'
done

# banner "ETAT DB: modules installés"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c \
# "SELECT name, state FROM ir_module_module WHERE name LIKE 'pdp_%' OR name LIKE 'rubicon_%' ORDER BY name;"

# banner "ETAT DB: modèles & champs (top 200)"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c "SELECT model, name FROM ir_model WHERE model LIKE 'pdp.%' ORDER BY model;"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c "SELECT model, name AS field, ttype FROM ir_model_fields WHERE model LIKE 'pdp.%' AND state='base' ORDER BY model, name LIMIT 200;"

# banner "ETAT DB: check données clés"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c "SELECT COUNT(*) AS products FROM pdp_product;"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c "SELECT COUNT(*) AS models FROM pdp_product_model;"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c "SELECT COUNT(*) AS matchings FROM pdp_product_model_matching;"

# banner "DEVISES: santé rapide"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c "SELECT name, symbol, rounding, active FROM res_currency ORDER BY name;"
# $DB psql -U "$DBUSER" -d "$DBNAME" -c "SELECT COUNT(*) AS rates_total, MIN(name) AS first_date, MAX(name) AS last_date FROM res_currency_rate;"

# banner "TEST RAPIDE PRICING (si tests présents)"
# docker compose exec odoo odoo -d "$DBNAME" -u pdp_price --test-enable --stop-after-init || true

banner "ERD (regen optionnelle via script maison)"
$ODOO python3 - <<'PY' || true
try:
    from rubicon_import.analysis import diagram as d
    d.main()
    print("[OK] ERD regénéré via rubicon_import.analysis.diagram")
except Exception as e:
    print("[SKIP] ERD non regénéré:", e)
PY

echo
echo "[OK] Audit terminé."
