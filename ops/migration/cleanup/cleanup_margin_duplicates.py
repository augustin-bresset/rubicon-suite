"""
Remove duplicate pdp.margin records that have no XML ID.
After the CSV was loaded, records with xmlids (pdp_margin.margin_X) were created
alongside pre-existing records without xmlids. Keep the CSV ones, delete the orphans.
"""

env = self.env  # noqa: F821 — injected by Odoo shell exec

Margin = env["pdp.margin"]
ModelData = env["ir.model.data"]

# Collect all margin IDs that are owned by an xmlid from the pdp_margin module
csv_ids = set(
    ModelData.search([("module", "=", "pdp_margin"), ("model", "=", "pdp.margin")]).mapped("res_id")
)

all_margins = Margin.search([])
orphans = all_margins.filtered(lambda m: m.id not in csv_ids)

if not orphans:
    print("No duplicate orphan margins found.")
else:
    print(f"Found {len(orphans)} orphan margin(s) to delete:")
    for m in orphans:
        print(f"  id={m.id}  code={m.code}  name={m.name}")
    orphans.unlink()
    env.cr.commit()
    print("Done.")
