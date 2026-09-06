"""Fold alt_code_computed into alt_code with a provenance column.

One alternative code per record, its source telling official (assigned by
the new system, never overwritten by a recompute) from computed (derived
by the converter). Existing computed values move into alt_code where no
official value stands; the redundant column is dropped.
"""


def migrate(cr, version):
    cr.execute("""
        SELECT table_name FROM information_schema.columns
        WHERE table_schema = 'public' AND column_name = 'alt_code_computed'
    """)
    for (table,) in cr.fetchall():
        cr.execute('ALTER TABLE "%s" ADD COLUMN IF NOT EXISTS alt_code_source varchar' % table)
        cr.execute("""
            UPDATE "%s" SET alt_code_source = 'official'
            WHERE alt_code IS NOT NULL AND alt_code_source IS NULL
        """ % table)
        cr.execute("""
            UPDATE "%s" SET alt_code = alt_code_computed, alt_code_source = 'computed'
            WHERE alt_code IS NULL AND alt_code_computed IS NOT NULL
        """ % table)
        cr.execute('ALTER TABLE "%s" DROP COLUMN alt_code_computed' % table)
