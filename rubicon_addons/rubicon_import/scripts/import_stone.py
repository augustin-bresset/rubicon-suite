# scripts/stone_import.py
# Script to run via:  odoo shell -d <db> < scripts/stone_import.py
# In odoo shell, 'env' is already provided.

# Try the "clean" import...
if not env:
    raise "ENV not defined."
    
try:
    from odoo.addons.rubicon_import.import_scripts.generic import import_csv
except Exception:
    # ...otherwise fall back to an absolute path (zero PYTHONPATH dependency)
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
print("[SUCCESS] STONE import done.")
