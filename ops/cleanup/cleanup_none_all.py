"""
Remove "None" (code=0) and "All" (code=1) placeholder records from reference tables.

These are relics from the old SQL Server database where code=0 meant "unspecified"
and code=1 meant "all/any". They have no meaning in the new Odoo data model.

For each record found:
  1. Nullable M2O fields pointing to it are set to NULL (False in Odoo).
  2. Fields marked action="delete" delete the referencing row entirely.
  3. Fields marked action="skip" (required, cannot nullify) block target deletion.
  4. The target record is deleted only if no "skip" references remain.

Run
---
  make cleanup-none-all
  # or directly:
  docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/cleanup/cleanup_none_all.py
"""

# ── Config ────────────────────────────────────────────────────────────────────

# (target_model, [(source_model, field_name, action), ...])
# action: "nullify" | "delete" (delete the referencing row) | "skip" (required, blocks target deletion)
TARGETS = [
    ("pdp.addon.type", [
        ("pdp.addon.cost",    "addon_id",  "nullify"),
        ("pdp.margin.addon",  "addon_id",  "nullify"),
    ]),
    ("pdp.metal", [
        ("pdp.product.model.metal", "metal_id", "nullify"),
        ("pdp.metal.parameter",     "metal_id", "nullify"),
    ]),
    ("pdp.product.category", [
        ("pdp.product",       "category_id", "nullify"),
        ("pdp.product.model", "category_id", "nullify"),
    ]),
    ("pdp.stone.shade", [
        ("pdp.stone",        "shade_id", "nullify"),
        ("pdp.stone.weight", "shade_id", "nullify"),
    ]),
    ("pdp.stone.shape", [
        ("pdp.stone",         "shape_id",         "skip"),    # required on pdp.stone
        ("pdp.stone.weight",  "shape_id",          "skip"),    # required on pdp.stone.weight
        ("pdp.product.stone", "reshaped_shape_id", "nullify"),
    ]),
    ("pdp.stone.type", [
        ("pdp.stone",        "type_id",       "skip"),    # required on pdp.stone
        ("pdp.stone.weight", "type_id",       "skip"),    # required on pdp.stone.weight
        ("pdp.margin.stone", "stone_type_id", "delete"),  # margin rows for None/All type are meaningless
    ]),
]

# ── Phase 1: Diagnose ─────────────────────────────────────────────────────────

print("=" * 60)
print("PHASE 1 — Diagnosis")
print("=" * 60)

total_refs = 0
plan = []       # (action, target_records, source_model, field_name, referencing_records)
blocked = {}    # target_model -> count of skip references that block deletion

for target_model, sources in TARGETS:
    if target_model not in env.registry.models:
        print(f"\n  [SKIP] {target_model} — model not installed")
        continue

    targets = env[target_model].search([("code", "in", ["0", "1"])])
    targets = targets.filtered(lambda r: r.display_name in ("None", "All", "0", "1"))

    if not targets:
        print(f"\n  {target_model}: no None/All records found")
        continue

    print(f"\n  {target_model}: {len(targets)} record(s) to delete")
    for r in targets:
        print(f"    id={r.id}  code={r.code}  name={r.display_name}")

    blocked_count = 0
    for src_model, field, action in sources:
        if src_model not in env.registry.models:
            continue
        refs = env[src_model].search([(field, "in", targets.ids)])
        count = len(refs)
        total_refs += count
        tag = f" [{action.upper()}]" if action != "nullify" else ""
        status = f"{count} reference(s)" if count else "no references"
        print(f"    └─ {src_model}.{field}: {status}{tag}")
        if count:
            plan.append((action, targets, src_model, field, refs))
        if count and action == "skip":
            blocked_count += count
    if blocked_count:
        blocked[target_model] = blocked_count

print(f"\nTotal references found: {total_refs}")
if blocked:
    print("Blocked (required fields — target record kept):")
    for m, c in blocked.items():
        print(f"  {m}: {c} required reference(s)")

# ── Phase 2: Clean ────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("PHASE 2 — Cleanup")
print("=" * 60)

nullified = deleted_refs = deleted = 0

for action, targets, src_model, field, refs in plan:
    if action == "nullify":
        refs.write({field: False})
        print(f"  Nullified {len(refs)} {src_model}.{field}")
        nullified += len(refs)
    elif action == "delete":
        count = len(refs)
        refs.unlink()
        print(f"  Deleted {count} {src_model} row(s) (field={field})")
        deleted_refs += count
    # action == "skip": nothing to do

env.cr.commit()
print(f"\n  committed {nullified} nullifications")

for target_model, sources in TARGETS:
    if target_model not in env.registry.models:
        continue
    if target_model in blocked:
        print(f"  Kept {target_model} (required references remain)")
        continue
    targets = env[target_model].search([("code", "in", ["0", "1"])])
    targets = targets.filtered(lambda r: r.display_name in ("None", "All", "0", "1"))
    if not targets:
        continue
    count = len(targets)
    try:
        targets.unlink()
        print(f"  Deleted {count} record(s) from {target_model}")
        deleted += count
    except Exception as exc:
        print(f"  Could not delete from {target_model}: {exc}")

env.cr.commit()

print(f"\nDone. nullified={nullified}, deleted_refs={deleted_refs}, deleted_targets={deleted}")
if blocked:
    print("Note: shape/type None-All records kept because their references cannot be nullified (required fields).")
