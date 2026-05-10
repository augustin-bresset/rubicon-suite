"""
Restore closed/canceled flags on sis.document records from the source CSV.

Run with:
    make shell < ops/restore_doc_flags.py
"""

import sys
import csv

env = env  # noqa

CSV_PATH = "/mnt/extra-addons/sis_document/data/sis.document.csv"

with open(CSV_PATH, newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

updated = 0
for row in rows:
    name = row.get('name', '').strip()
    closed   = row.get('closed',   'False').strip() == 'True'
    canceled = row.get('canceled', 'False').strip() == 'True'

    env.cr.execute(
        "UPDATE sis_document SET closed=%s, canceled=%s WHERE name=%s",
        (closed, canceled, name)
    )
    updated += env.cr.rowcount

env.cr.commit()
print(f"Done. Updated {updated} document records.")
sys.exit(0)
