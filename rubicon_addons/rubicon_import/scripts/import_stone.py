# scripts/stone_import.py
# Script à exécuter via:  odoo shell -d <db> < scripts/stone_import.py
# Dans odoo shell, 'env' est déjà fourni.

# On essaie l'import "propre"...
if not env:
    
try:
    from odoo.addons.rubicon_import.import_scripts.generic import import_csv
except Exception:
    # ...sinon fallback par chemin absolu (zéro dépendance PYTHONPATH)
    import importlib.util
    PATH = "/mnt/extra-addons/rubicon_import/import_scripts/generic.py"
    spec = importlib.util.spec_from_file_location("generic", PATH)
    generic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generic)
    import_csv = generic.import_csv

env.cr.autocommit = False

MODELS = [
    "pdp.stone.category",
    "pdp.stone.type",
    "pdp.stone.shape",
    "pdp.stone.shade",
    "pdp.stone.size",
    "pdp.stone.weight",
    "pdp.stone",
]

for model in MODELS:
    import_csv(env, env[model], "pdp_stone")

env.cr.commit()
print("✅ STONE import done.")
