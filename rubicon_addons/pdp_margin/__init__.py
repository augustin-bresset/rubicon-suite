import logging

from . import models

_logger = logging.getLogger(__name__)


def post_init(env):
    """Seed initial margin data. Safe to re-run: creates only what is missing."""
    import csv
    import os

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

    def read_csv(filename):
        path = os.path.join(DATA_DIR, filename)
        with open(path) as f:
            return list(csv.DictReader(f))

    def by_code(model, field="code"):
        return {r[field]: r.id for r in env[model].search([])}

    # --- Margins (upsert by code) ---
    existing_margins = by_code("pdp.margin")
    for row in read_csv("pdp.margin.csv"):
        if row["code"] not in existing_margins:
            rec = env["pdp.margin"].create({
                "code": row["code"],
                "name": row["name"],
                "labor_metal_rate": float(row["labor_metal_rate"] or 1.0),
                "labor_stone_rate": float(row["labor_stone_rate"] or 1.0),
            })
            existing_margins[row["code"]] = rec.id

    margins      = existing_margins
    addon_types  = by_code("pdp.addon.type")
    purities     = by_code("pdp.metal.purity")
    stone_types  = by_code("pdp.stone.type")
    stone_cats   = by_code("pdp.stone.category")
    stone_shapes = by_code("pdp.stone.shape")
    stone_sizes  = by_code("pdp.stone.size", field="name")
    stone_shades = by_code("pdp.stone.shade")
    currencies   = by_code("res.currency", field="name")

    # Build sets of existing sub-records to avoid duplicates
    def existing_pairs(model, f1, f2):
        return {(r[f1].id, r[f2].id) for r in env[model].search([])}

    existing_parts  = {r.margin_id.id for r in env["pdp.margin.part"].search([])}
    existing_addons = existing_pairs("pdp.margin.addon", "margin_id", "addon_id")
    existing_metals = existing_pairs("pdp.margin.metal", "margin_id", "metal_purity_id")
    existing_stones = existing_pairs("pdp.margin.stone", "margin_id", "stone_type_id")

    existing_conds = {
        (r.margin_id.id, r.stone_cat_id.id)
        for r in env["pdp.margin.stone.conditional"].search([])
    }

    # --- Parts ---
    for row in read_csv("pdp.margin.part.csv"):
        mid = margins.get(row["margin_id"])
        if mid and mid not in existing_parts:
            env["pdp.margin.part"].create({"margin_id": mid, "rate": float(row["rate"] or 0)})
            existing_parts.add(mid)

    # --- Addons ---
    for row in read_csv("pdp.margin.addon.csv"):
        mid = margins.get(row["margin_id"])
        aid = addon_types.get(row["addon_id"])
        if mid and aid and (mid, aid) not in existing_addons:
            env["pdp.margin.addon"].create({"margin_id": mid, "addon_id": aid, "rate": float(row["rate"] or 0)})
            existing_addons.add((mid, aid))

    # --- Metals ---
    for row in read_csv("pdp.margin.metal.csv"):
        mid = margins.get(row["margin_id"])
        pid = purities.get(row["metal_purity_id"])
        if mid and pid and (mid, pid) not in existing_metals:
            env["pdp.margin.metal"].create({"margin_id": mid, "metal_purity_id": pid, "rate": float(row["rate"] or 0)})
            existing_metals.add((mid, pid))

    # --- Stones ---
    for row in read_csv("pdp.margin.stone.csv"):
        mid  = margins.get(row["margin_id"])
        stid = stone_types.get(row["stone_type_id"])
        if not mid or not stid or (mid, stid) in existing_stones:
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
        env["pdp.margin.stone"].create(vals)
        existing_stones.add((mid, stid))

    # --- Stone Conditionals ---
    for row in read_csv("pdp.margin.stone.conditional.csv"):
        mid  = margins.get(row["margin_id"])
        scid = stone_cats.get(row["stone_cat_id"])
        if not mid or not scid or (mid, scid) in existing_conds:
            continue
        vals = {
            "margin_id": mid,
            "stone_cat_id": scid,
            "operator": row["operator"],
            "comparative_cost": float(row["comparative_cost"] or 0),
            "rate": float(row["rate"] or 0),
        }
        cid = currencies.get(row["currency_id"])
        if cid: vals["currency_id"] = cid
        env["pdp.margin.stone.conditional"].create(vals)
        existing_conds.add((mid, scid))

    env.cr.commit()
    _logger.info("pdp_margin post_init: margin seed data ensured")
