# scripts/update_stone_settings.py
# Run via:  odoo shell -d rubicon < scripts/update_stone_settings.py
#
# Updates pdp.product.stone records with setting_type_id from ModelStone.csv
# (column 4 = numeric setting ID → pdp.stone.setting.type external ID)

import csv, os

if not env:
    raise RuntimeError("env not defined — run via odoo shell")

SOURCE = "/mnt/extra-addons/../../../data/backup_pdp/ModelStone.csv"
if not os.path.exists(SOURCE):
    SOURCE = "/home/smaug/rubicon-suite/data/backup_pdp/ModelStone.csv"

# Build a map: external_id → setting_type record
setting_type_by_num = {}
for rec in env["pdp.stone.setting.type"].search([]):
    # Find the ir.model.data entry for this record
    imd = env["ir.model.data"].search([
        ("model", "=", "pdp.stone.setting.type"),
        ("res_id", "=", rec.id),
        ("module", "=", "pdp_stone"),
    ], limit=1)
    if imd:
        # external ID is like "setting_type_2" → extract the number
        num = imd.name.replace("setting_type_", "")
        setting_type_by_num[num] = rec

print(f"[INFO] Loaded {len(setting_type_by_num)} setting types: {list(setting_type_by_num.keys())[:10]}")

# Also build a map of existing product stone records by (composition_code, stone_code)
# We need the same code generation logic as in the import
sys_path_backup = None
try:
    from odoo.addons.rubicon_import.tools.standard import (
        func_index, create_product_composition_code, create_stone_code,
        size_field, strip_code_space
    )
    from odoo.addons.rubicon_import.tools.parsing import safe_int, safe_float
    HAS_IMPORT_TOOLS = True
except ImportError:
    HAS_IMPORT_TOOLS = False
    print("[WARNING] rubicon_import tools not available — using fallback")


def strip_cs(s):
    return s.strip().replace(" ", "")


def size_f(s):
    s = strip_cs(s)
    if not s or s in {"0", "None", "NONE"}:
        return ""
    return s


updated = skipped = errors = 0

with open(SOURCE, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row_raw in reader:
        # Handle two-line rows (same logic as raw_to_data_product.py)
        row = list(row_raw)
        if row[2] in {"P", "W"} and len(row) > 3:
            row[2] = f"{row[2]}.{row[3]}"
            for i in range(3, len(row) - 1):
                row[i] = row[i + 1]
            del row[-1]

        if len(row) < 9:
            continue

        try:
            int(row[8])   # pieces must be int
        except (ValueError, IndexError):
            continue

        category_code = strip_cs(row[0])
        reference_code = strip_cs(row[1])
        stone_colors_code = strip_cs(row[2])
        stone_type_code = strip_cs(row[3])
        setting_num = strip_cs(row[4]) if len(row) > 4 else ""
        stone_shape_code = strip_cs(row[5])
        stone_size = size_f(row[6])
        stone_shade_code = strip_cs(row[7])

        if not setting_num or setting_num in {"0", "1"}:
            continue  # no setting type to set

        setting_rec = setting_type_by_num.get(setting_num)
        if not setting_rec:
            continue

        # Rebuild composition code (same formula as import)
        comp_code = f"{category_code}{reference_code}-{stone_colors_code}"

        # Rebuild stone code (type+shade+shape+size)
        no_all = lambda s: "" if s in {"ALL", "all", "1", "0", ""} else s
        shade = no_all(stone_shade_code)
        stone_code_parts = [stone_type_code]
        if shade:
            stone_code_parts.append(shade)
        stone_code_parts.append(stone_shape_code)
        if stone_size:
            stone_code_parts.append(stone_size)
        stone_code = "-".join(stone_code_parts)

        # Find matching product stone record
        comp = env["pdp.product.stone.composition"].search(
            [("code", "=", comp_code)], limit=1
        )
        if not comp:
            skipped += 1
            continue

        stone_cat = env["pdp.stone"].search([("code", "=", stone_code)], limit=1)
        if not stone_cat:
            skipped += 1
            continue

        lines = env["pdp.product.stone"].search([
            ("composition_id", "=", comp.id),
            ("stone_id", "=", stone_cat.id),
        ])
        if not lines:
            skipped += 1
            continue

        try:
            lines.write({"setting_type_id": setting_rec.id, "setting": setting_rec.cost})
            updated += len(lines)
        except Exception as e:
            errors += 1
            print(f"[ERROR] {comp_code}/{stone_code}: {e}")

env.cr.commit()
print(f"[DONE] updated={updated} skipped={skipped} errors={errors}")
