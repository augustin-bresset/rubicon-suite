"""
Cleanup duplicate SIS lookup records created by double module upgrades.

Run with:
    make shell < ops/cleanup_sis_lookups.py

Strategy: keep lowest-ID record for each name, remap FK references,
then delete the higher-ID duplicates.
"""

import sys

env = env  # noqa: provided by odoo shell

def dedup_model(model_name, table_name, fk_refs):
    """
    Remove duplicate records by keeping the lowest id per name.
    fk_refs: list of (model, field) pairs that reference this table.
    """
    records = env[model_name].search([], order='id')
    seen = {}   # name -> record to keep
    to_delete = env[model_name].browse()

    for rec in records:
        key = rec.name
        if key not in seen:
            seen[key] = rec
        else:
            # this is a duplicate — remap FKs then delete
            keep_id = seen[key].id
            dup_id = rec.id
            for (ref_model, ref_field) in fk_refs:
                ref_table = env[ref_model]._table
                env.cr.execute(
                    f"UPDATE {ref_table} SET {ref_field} = %s WHERE {ref_field} = %s",
                    (keep_id, dup_id)
                )
            to_delete |= rec

    if to_delete:
        print(f"[{model_name}] Deleting {len(to_delete)} duplicate(s): ids={to_delete.ids}")
        to_delete.unlink()
    else:
        print(f"[{model_name}] No duplicates found.")

# --- sis.pay.term ---
dedup_model(
    'sis.pay.term',
    'sis_pay_term',
    [
        ('sis.document', 'pay_term_id'),
        ('res.partner', 'sis_pay_term_id'),
        ('res.partner', 'sis_vendor_pay_term_id'),
    ]
)

# --- sis.doc.in.mode ---
dedup_model(
    'sis.doc.in.mode',
    'sis_doc_in_mode',
    [
        ('sis.document', 'rcv_mode_id'),
    ]
)

# --- sis.trade.fair ---
dedup_model(
    'sis.trade.fair',
    'sis_trade_fair',
    [
        ('sis.document', 'trade_fair_id'),
    ]
)

# --- Link SO-EMA-25001 → SI-EMA-25003 as child document ---
so = env['sis.document'].search([('name', '=', 'SO-EMA-25001')], limit=1)
si = env['sis.document'].search([('name', '=', 'SI-EMA-25003')], limit=1)
if so and si:
    if si not in so.child_doc_ids:
        so.child_doc_ids = [(4, si.id)]
        print(f"Linked {si.name} as child of {so.name}.")
    else:
        print(f"{si.name} already linked to {so.name}.")
else:
    print(f"WARNING: could not find SO-EMA-25001 ({bool(so)}) or SI-EMA-25003 ({bool(si)}).")

env.cr.commit()
print("Done.")
sys.exit(0)
