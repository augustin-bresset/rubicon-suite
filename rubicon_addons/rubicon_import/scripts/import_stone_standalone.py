#!/usr/bin/env python3
import argparse, importlib.util
import odoo
from odoo import api

def load_import_csv():
    try:
        from odoo.addons.rubicon_import.import_scripts.generic import import_csv
        return import_csv
    except Exception:
        PATH = "/mnt/extra-addons/rubicon_import/import_scripts/generic.py"
        spec = importlib.util.spec_from_file_location("generic", PATH)
        generic = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generic)
        return getattr(generic, "import_csv")

def main(db, conf):
    # Boot Odoo
    odoo.tools.config.parse_config(["-d", db, "-c", conf])
    import_csv = load_import_csv()

    with api.Environment.manage():
        registry = odoo.registry(db)
        with registry.cursor() as cr:
            env = api.Environment(cr, 1, {})  # SUPERUSER_ID = 1
            for model in [
                "pdp.stone.category",
                "pdp.stone.type",
                "pdp.stone.shape",
                "pdp.stone.shade",
                "pdp.stone.size",
                "pdp.stone.weight",
                "pdp.stone",
            ]:
                import_csv(env, env[model], "pdp_stone")
            cr.commit()
    print("[SUCCESS] STONE import done.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--db", default="rubicon")
    ap.add_argument("-c", "--config", default="/etc/odoo/odoo.conf")
    args = ap.parse_args()
    main(args.db, args.config)
