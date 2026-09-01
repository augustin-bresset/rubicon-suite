"""
Restore pdp.margin sub-records from CSVs in pdp_margin/data/.
Resolves codes to DB IDs. Safe to re-run: skips existing records by xmlid.
"""
import csv
import os

env = self.env  # noqa: F821
DATA_DIR = "/mnt/extra-addons/pdp_margin/data"

ModelData = env["ir.model.data"]

def get_xmlid_res_ids(model):
    recs = ModelData.search([("module", "=", "pdp_margin"), ("model", "=", model)])
    return {r.name: r.res_id for r in recs}

def ensure_xmlid(module, name, model, res_id):
    existing = ModelData.search([("module", "=", module), ("name", "=", name)])
    if not existing:
        ModelData.create({"module": module, "name": name, "model": model, "res_id": res_id})

def by_code(model, field="code"):
    return {r[field]: r.id for r in env[model].search([])}

def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path) as f:
        return list(csv.DictReader(f))

# --- Build lookup tables ---
margins     = by_code("pdp.margin")
addon_types = by_code("pdp.addon.type")
purities    = by_code("pdp.metal.purity")
stone_types = by_code("pdp.stone.type")
stone_cats  = by_code("pdp.stone.category")
stone_shapes= by_code("pdp.stone.shape")
stone_sizes = by_code("pdp.stone.size")
stone_shades= by_code("pdp.stone.shade")
currencies  = by_code("res.currency", field="name")

existing_parts   = get_xmlid_res_ids("pdp.margin.part")
existing_addons  = get_xmlid_res_ids("pdp.margin.addon")
existing_metals  = get_xmlid_res_ids("pdp.margin.metal")
existing_stones  = get_xmlid_res_ids("pdp.margin.stone")
existing_conds   = get_xmlid_res_ids("pdp.margin.stone.conditional")

created = {"part": 0, "addon": 0, "metal": 0, "stone": 0, "conditional": 0}

# --- Parts ---
for row in read_csv("pdp.margin.part.csv"):
    xid = row["id"]
    if xid in existing_parts:
        continue
    mid = margins.get(row["margin_id"])
    if not mid:
        print(f"  SKIP part {xid}: margin '{row['margin_id']}' not found")
        continue
    rec = env["pdp.margin.part"].create({"margin_id": mid, "rate": float(row["rate"] or 0)})
    ensure_xmlid("pdp_margin", xid, "pdp.margin.part", rec.id)
    created["part"] += 1

# --- Addons ---
for row in read_csv("pdp.margin.addon.csv"):
    xid = row["id"]
    if xid in existing_addons:
        continue
    mid = margins.get(row["margin_id"])
    aid = addon_types.get(row["addon_id"])
    if not mid or not aid:
        print(f"  SKIP addon {xid}: margin='{row['margin_id']}' addon='{row['addon_id']}'")
        continue
    rec = env["pdp.margin.addon"].create({"margin_id": mid, "addon_id": aid, "rate": float(row["rate"] or 0)})
    ensure_xmlid("pdp_margin", xid, "pdp.margin.addon", rec.id)
    created["addon"] += 1

# --- Metals ---
for row in read_csv("pdp.margin.metal.csv"):
    xid = row["id"]
    if xid in existing_metals:
        continue
    mid = margins.get(row["margin_id"])
    pid = purities.get(row["metal_purity_id"])
    if not mid or not pid:
        print(f"  SKIP metal {xid}: margin='{row['margin_id']}' purity='{row['metal_purity_id']}'")
        continue
    rec = env["pdp.margin.metal"].create({"margin_id": mid, "metal_purity_id": pid, "rate": float(row["rate"] or 0)})
    ensure_xmlid("pdp_margin", xid, "pdp.margin.metal", rec.id)
    created["metal"] += 1

# --- Stones ---
for row in read_csv("pdp.margin.stone.csv"):
    xid = row["id"]
    if xid in existing_stones:
        continue
    mid = margins.get(row["margin_id"])
    stid = stone_types.get(row["stone_type_id"])
    if not mid or not stid:
        print(f"  SKIP stone {xid}: margin='{row['margin_id']}' type='{row['stone_type_id']}'")
        continue
    vals = {"margin_id": mid, "stone_type_id": stid, "rate": float(row["rate"] or 0)}
    if row.get("stone_shape_id"):
        sid = stone_shapes.get(row["stone_shape_id"])
        if sid: vals["stone_shape_id"] = sid
    if row.get("stone_size_id"):
        sid = stone_sizes.get(row["stone_size_id"])
        if sid: vals["stone_size_id"] = sid
    if row.get("stone_shade_id"):
        sid = stone_shades.get(row["stone_shade_id"])
        if sid: vals["stone_shade_id"] = sid
    rec = env["pdp.margin.stone"].create(vals)
    ensure_xmlid("pdp_margin", xid, "pdp.margin.stone", rec.id)
    created["stone"] += 1

# --- Stone Conditionals ---
for row in read_csv("pdp.margin.stone.conditional.csv"):
    xid = row["id"]
    if xid in existing_conds:
        continue
    mid  = margins.get(row["margin_id"])
    scid = stone_cats.get(row["stone_cat_id"])
    cid  = currencies.get(row["currency_id"])
    if not mid or not scid:
        print(f"  SKIP conditional {xid}: margin='{row['margin_id']}' cat='{row['stone_cat_id']}'")
        continue
    vals = {
        "margin_id": mid, "stone_cat_id": scid,
        "operator": row["operator"],
        "comparative_cost": float(row["comparative_cost"] or 0),
        "rate": float(row["rate"] or 0),
    }
    if cid: vals["currency_id"] = cid
    rec = env["pdp.margin.stone.conditional"].create(vals)
    ensure_xmlid("pdp_margin", xid, "pdp.margin.stone.conditional", rec.id)
    created["conditional"] += 1

env.cr.commit()
print(f"\nDone. Created: {created}")
