from collections import defaultdict

groups = defaultdict(list)
for t in env['sis.doc.type'].search([]):
    groups[t.name].append(t)

found = False
for name, records in groups.items():
    if len(records) > 1:
        found = True
        with_xid = [r for r in records if env['ir.model.data'].search([('model','=','sis.doc.type'),('res_id','=',r.id)])]
        without_xid = [r for r in records if r not in with_xid]
        print(f"'{name}': {len(records)} records — keeping {[r.id for r in with_xid]}, deleting {[r.id for r in without_xid]}")
        for r in without_xid:
            r.unlink()

if not found:
    print("No duplicates found.")

env.cr.commit()
print("Done.")
