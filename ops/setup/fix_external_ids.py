"""
Fix duplicate reference records and missing ir.model.data external IDs.

Run via:
    docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/setup/fix_external_ids.py
"""
import csv as _csv
import os as _os
import re as _re

CSV_DIR = '/mnt/extra-addons/pdp_stone/data'


def ensure_external_id(env, module, ext_name, model, domain):
    """Link an existing record to its external ID if the link is missing."""
    existing_xid = env['ir.model.data'].search([
        ('module', '=', module), ('name', '=', ext_name),
    ], limit=1)
    if existing_xid:
        return False
    record = env[model].search(domain, limit=1)
    if not record:
        return False
    env['ir.model.data'].create({
        'module': module, 'name': ext_name,
        'model': model, 'res_id': record.id, 'noupdate': True,
    })
    return True


def dedup_model(env, model, code_field, fk_fields):
    """
    Remove duplicate records, keeping the one with the lowest ID (first created).
    Rewires any FK references from duplicates to the kept record before deleting.
    fk_fields: list of (related_model, field_name) tuples
    """
    records = env[model].search([], order='id asc')
    seen = {}
    removed = 0
    for rec in records:
        code = getattr(rec, code_field)
        if code in seen:
            keep = seen[code]
            for rel_model, rel_field in fk_fields:
                refs = env[rel_model].search([(rel_field, '=', rec.id)])
                if refs:
                    refs.write({rel_field: keep.id})
                    print(f"  Rewired {len(refs)} {rel_model}.{rel_field} from id={rec.id} to id={keep.id}")
            env['ir.model.data'].search([('model', '=', model), ('res_id', '=', rec.id)]).unlink()
            rec.unlink()
            removed += 1
            print(f"  Removed duplicate {model} code={code} id={rec.id} (kept id={keep.id})")
        else:
            seen[code] = rec
    return removed


def bulk_create_xids(env, module, model, pairs):
    """Create ir.model.data records in bulk. pairs: list of (xid_name, res_id)."""
    if not pairs:
        return 0
    env['ir.model.data'].create([{
        'module': module, 'name': name,
        'model': model, 'res_id': res_id, 'noupdate': True,
    } for name, res_id in pairs])
    return len(pairs)


def existing_xids_set(env, module, model):
    return set(env['ir.model.data'].search([
        ('module', '=', module), ('model', '=', model)
    ]).mapped('name'))


# ---------------------------------------------------------------------------
print("=" * 60)
print("Step 1: Remove duplicate pdp.labor.type records")
print("=" * 60)
n = dedup_model(env, 'pdp.labor.type', 'code', [
    ('pdp.labor.cost.model', 'labor_id'),
    ('pdp.labor.cost.product', 'labor_id'),
    ('pdp.margin.labor', 'labor_id'),
])
print(f"  → {n} duplicates removed\n")

print("=" * 60)
print("Step 2: Remove duplicate pdp.addon.type records")
print("=" * 60)
n = dedup_model(env, 'pdp.addon.type', 'code', [
    ('pdp.addon.cost', 'addon_id'),
    ('pdp.margin.addon', 'addon_id'),
])
print(f"  → {n} duplicates removed\n")

print("=" * 60)
print("Step 3: Remove duplicate pdp.stone.* reference records")
print("=" * 60)
n = dedup_model(env, 'pdp.stone.category', 'code', [
    ('pdp.stone.type', 'category_id'),
])
print(f"  → {n} pdp.stone.category duplicates removed")

n = dedup_model(env, 'pdp.stone.type', 'code', [
    ('pdp.stone.weight', 'type_id'),
    ('pdp.product.stone', 'type_id'),
])
print(f"  → {n} pdp.stone.type duplicates removed")

n = dedup_model(env, 'pdp.stone.shape', 'code', [
    ('pdp.stone.weight', 'shape_id'),
    ('pdp.product.stone', 'reshaped_shape_id'),
])
print(f"  → {n} pdp.stone.shape duplicates removed")

n = dedup_model(env, 'pdp.stone.shade', 'code', [
    ('pdp.stone.weight', 'shade_id'),
])
print(f"  → {n} pdp.stone.shade duplicates removed")

n = dedup_model(env, 'pdp.stone.size', 'name', [
    ('pdp.stone', 'size_id'),
    ('pdp.stone.weight', 'size_id'),
    ('pdp.product.stone', 'reshaped_size_id'),
])
print(f"  → {n} pdp.stone.size duplicates removed\n")

# ---------------------------------------------------------------------------
print("=" * 60)
print("Step 4: Align pdp.stone.size xids with CSV (case mismatch fix)")
print("=" * 60)

size_csv_path = _os.path.join(CSV_DIR, 'pdp.stone.size.csv')
existing_size_xids = existing_xids_set(env, 'pdp_stone', 'pdp.stone.size')
size_by_name = {r.name: r.id for r in env['pdp.stone.size'].search([])}
# xid→rec_id lookup for rename
xid_rec = {x.name: x for x in env['ir.model.data'].search([
    ('module', '=', 'pdp_stone'), ('model', '=', 'pdp.stone.size')
])}
aligned = 0
with open(size_csv_path, newline='') as f:
    for row in _csv.DictReader(f):
        csv_id = row['id']
        if csv_id in existing_size_xids:
            continue
        name_val = row['name']
        rec_id = size_by_name.get(name_val)
        if not rec_id:
            continue
        # Find any existing xid for this rec and rename it
        old_xid = env['ir.model.data'].search([
            ('module', '=', 'pdp_stone'), ('model', '=', 'pdp.stone.size'),
            ('res_id', '=', rec_id),
        ], limit=1)
        if old_xid:
            old_name = old_xid.name
            old_xid.write({'name': csv_id})
            existing_size_xids.add(csv_id)
            aligned += 1
        else:
            env['ir.model.data'].create({
                'module': 'pdp_stone', 'name': csv_id,
                'model': 'pdp.stone.size', 'res_id': rec_id, 'noupdate': True,
            })
            existing_size_xids.add(csv_id)
            aligned += 1

print(f"  → {aligned} size xids aligned\n")

# ---------------------------------------------------------------------------
print("=" * 60)
print("Step 5: Create ir.model.data for pdp.stone and pdp.stone.weight")
print("=" * 60)

# Build reference lookups
types  = {r.code: r.id for r in env['pdp.stone.type'].search([])}
shapes = {r.code: r.id for r in env['pdp.stone.shape'].search([])}
shades = {r.code: r.id for r in env['pdp.stone.shade'].search([])}
sizes  = {r.name: r.id for r in env['pdp.stone.size'].search([])}

# --- pdp.stone ---
existing_stone_xids = existing_xids_set(env, 'pdp_stone', 'pdp.stone')
stone_by_code = {s.code: s.id for s in env['pdp.stone'].search([])}
stone_csv_path = _os.path.join(CSV_DIR, 'pdp.stone.csv')
stone_pairs = []
stone_missing = 0
with open(stone_csv_path, newline='') as f:
    for row in _csv.DictReader(f):
        csv_id = row['id']
        if csv_id in existing_stone_xids:
            continue
        rec_id = stone_by_code.get(row['code'])
        if rec_id:
            stone_pairs.append((csv_id, rec_id))
        else:
            stone_missing += 1
n = bulk_create_xids(env, 'pdp_stone', 'pdp.stone', stone_pairs)
print(f"  → {n} pdp.stone xids created, {stone_missing} unmatched")

# --- pdp.stone.weight ---
existing_weight_xids = existing_xids_set(env, 'pdp_stone', 'pdp.stone.weight')
weights_by_key = {(w.type_id.id, w.shape_id.id, w.shade_id.id, w.size_id.id): w.id
                  for w in env['pdp.stone.weight'].search([])}
weight_csv_path = _os.path.join(CSV_DIR, 'pdp.stone.weight.csv')
weight_pairs = []
w_missing = 0
with open(weight_csv_path, newline='') as f:
    for row in _csv.DictReader(f):
        csv_id = row['id']
        if csv_id in existing_weight_xids:
            continue
        tid      = types.get(row['type_id'])
        sid_shp  = shapes.get(row['shape_id'])
        sid_shd  = shades.get(row['shade_id'])
        sid_size = sizes.get(row['size_id'])
        if not all([tid, sid_shp, sid_shd, sid_size]):
            w_missing += 1
            continue
        rec_id = weights_by_key.get((tid, sid_shp, sid_shd, sid_size))
        if rec_id:
            weight_pairs.append((csv_id, rec_id))
        else:
            w_missing += 1
n = bulk_create_xids(env, 'pdp_stone', 'pdp.stone.weight', weight_pairs)
print(f"  → {n} pdp.stone.weight xids created, {w_missing} unmatched\n")

# ---------------------------------------------------------------------------
print("=" * 60)
print("Step 6: Create missing ir.model.data for other reference data")
print("=" * 60)
fixed = 0

def safe_xid(s):
    return _re.sub(r'[^a-zA-Z0-9_]', '_', s)

# pdp.stone.category
STONE_CATS = [
    ('category_1', '1'), ('category_D', 'D'), ('category_H', 'H'),
    ('category_P', 'P'), ('category_R', 'R'), ('category_S', 'S'),
]
for ext_id, code in STONE_CATS:
    if ensure_external_id(env, 'pdp_stone', ext_id, 'pdp.stone.category', [('code', '=', code)]):
        print(f"  Fixed pdp.stone.category code={code}")
        fixed += 1

for rec in env['pdp.stone.shape'].search([]):
    ext_id = f'shape_{safe_xid(rec.code)}'
    if ensure_external_id(env, 'pdp_stone', ext_id, 'pdp.stone.shape', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.stone.shape code={rec.code}")
        fixed += 1

for rec in env['pdp.stone.shade'].search([]):
    ext_id = f'shade_{safe_xid(rec.code)}'
    if ensure_external_id(env, 'pdp_stone', ext_id, 'pdp.stone.shade', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.stone.shade code={rec.code}")
        fixed += 1

for rec in env['pdp.stone.type'].search([]):
    ext_id = f'type_{safe_xid(rec.code)}'
    if ensure_external_id(env, 'pdp_stone', ext_id, 'pdp.stone.type', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.stone.type code={rec.code}")
        fixed += 1

for rec in env['pdp.labor.type'].search([]):
    ext_id = f'type_{rec.code}'
    if ensure_external_id(env, 'pdp_labor', ext_id, 'pdp.labor.type', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.labor.type code={rec.code}")
        fixed += 1

for rec in env['pdp.addon.type'].search([]):
    ext_id = f'type_{rec.code}'
    if ensure_external_id(env, 'pdp_labor', ext_id, 'pdp.addon.type', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.addon.type code={rec.code}")
        fixed += 1

for rec in env['pdp.metal.purity'].search([]):
    ext_id = f'purity_{rec.code}'
    if ensure_external_id(env, 'pdp_metal', ext_id, 'pdp.metal.purity', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.metal.purity code={rec.code}")
        fixed += 1

for rec in env['pdp.metal'].search([]):
    ext_id = f'metal_{rec.code}'
    if ensure_external_id(env, 'pdp_metal', ext_id, 'pdp.metal', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.metal code={rec.code}")
        fixed += 1

for rec in env['pdp.part'].search([]):
    ext_id = f'part_{rec.code}'
    if ensure_external_id(env, 'pdp_metal', ext_id, 'pdp.part', [('code', '=', rec.code)]):
        print(f"  Fixed pdp.part code={rec.code}")
        fixed += 1

print(f"  → {fixed} external IDs created\n")

# ---------------------------------------------------------------------------
env.cr.commit()
print("=" * 60)
print("Done. You can now run: make upgrade")
print("=" * 60)
