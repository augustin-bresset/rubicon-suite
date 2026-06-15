# ops/import/import_missing_labor.py
# Imports pdp.labor.cost.model records for models that currently have 0 labor entries.
# Reads ModelLabor.csv directly (bypasses raw_to_data).
# Run via: docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/import/import_missing_labor.py

import csv, os

SOURCE = "/home/smaug/rubicon-suite/data/backup_pdp/ModelLabor.csv"
if not os.path.exists(SOURCE):
    SOURCE = "/mnt/extra-addons/../../../data/backup_pdp/ModelLabor.csv"

LaborCost = env['pdp.labor.cost.model']
LaborType = env['pdp.labor.type']
Model     = env['pdp.product.model']
Currency  = env['res.currency']

# Pre-load lookups
labor_by_code = {lt.code: lt for lt in LaborType.search([])}
currency_by_name = {c.name: c for c in Currency.search([])}

currency_map = {'TH': 'THB', 'US': 'USD', '': 'THB'}

def map_currency(code):
    code = code.strip().upper()
    return currency_map.get(code, code)

# Models that already have labor entries — skip them
models_with_labor = set(LaborCost.search([]).mapped('model_id').ids)

LABOR_COLS = [
    (3, 'ASS'),
    (4, 'CAS'),
    (5, 'FIL'),
    (6, 'POL'),
]

created = skipped = errors = 0

with open(SOURCE, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) < 9:
            continue
        cat = row[0].strip()
        if not cat.isalpha():
            continue

        from odoo.addons.rubicon_import.tools.standard import create_model_code, strip_code_space, mapping_currency
        model_code = create_model_code(row[0], row[1])
        metal_code = strip_code_space(row[2])
        curr_name  = mapping_currency(row[7], default='THB')

        model = Model.search([('code', '=', model_code)], limit=1)
        if not model:
            skipped += 1
            continue

        if model.id in models_with_labor:
            skipped += 1
            continue

        currency = currency_by_name.get(curr_name)
        if not currency:
            skipped += 1
            continue

        for col_idx, labor_code in LABOR_COLS:
            try:
                cost = float(row[col_idx])
            except (ValueError, IndexError):
                continue
            if cost <= 0.0:
                continue

            labor = labor_by_code.get(labor_code)
            if not labor:
                continue

            try:
                LaborCost.create({
                    'model_id':   model.id,
                    'labor_id':   labor.id,
                    'metal':      metal_code,
                    'cost':       cost,
                    'currency_id': currency.id,
                })
                created += 1
            except Exception as e:
                errors += 1
                print(f"[ERROR] {model_code}/{labor_code}: {e}")

env.cr.commit()
print(f"[DONE] created={created} skipped={skipped} errors={errors}")
