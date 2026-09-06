"""Rename the Emasur-specific columns to their generic names.

The alternative system is issued from Emasur but is not Emasur itself, so
the fields became alt_code / alt_design. Renaming at SQL level keeps the
already backfilled history instead of letting the ORM drop and recreate
empty columns.
"""


def migrate(cr, version):
    for old, new in [('emasur_code', 'alt_code'), ('design_emasur', 'alt_design')]:
        cr.execute("""
            SELECT table_name FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = %s
        """, (old,))
        for (table,) in cr.fetchall():
            cr.execute("SELECT 1 FROM information_schema.columns "
                       "WHERE table_schema = 'public' AND table_name = %s AND column_name = %s",
                       (table, new))
            if not cr.fetchone():
                cr.execute('ALTER TABLE "%s" RENAME COLUMN "%s" TO "%s"' % (table, old, new))
