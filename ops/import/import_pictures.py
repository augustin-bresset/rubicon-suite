"""
Import pictures; create/update when model exists,
otherwise create an orphan picture (model_id = False).
Run with: docker compose exec -T odoo odoo shell -d <DB> < ops/import/import_picture.py
"""
import os, base64, hashlib, re

# Garde-fous
if 'pdp.picture' not in env.registry.models:
    raise RuntimeError("Module pdp_picture non installé.")

Picture = env['pdp.picture']
Model = env['pdp.product.model']

base_path = '/mnt/extra-addons/pictures'
if not os.path.isdir(base_path):
    raise RuntimeError(f"Dossier introuvable: {base_path}")

pat = re.compile(r'^(?P<code>[^.]+)\.(jpg|jpeg|png)$', re.I)

created = updated = skipped = orphaned = 0
total = 0

for fname in sorted(os.listdir(base_path)):
    m = pat.match(fname)
    if not m:
        continue
    total += 1

    code = (m.group('code') or '').upper()
    full = os.path.join(base_path, fname)

    with open(full, 'rb') as f:
        data = f.read()

    b64 = base64.b64encode(data)
    chk = hashlib.md5(data).hexdigest()

    # ✅ utiliser la bonne clé: 'code' (pas 'name')
    model = Model.search([('code', '=', code)], limit=1)

    vals = {
        'model_id': model.id if model else False,   # ← orphelin si pas de modèle
        'filename': fname,
        'image': b64,
        'checksum': chk,
    }

    if model:
        pic = Picture.search([('model_id', '=', model.id)], limit=1)
        if pic:
            if pic.checksum != chk:
                pic.write(vals); updated += 1
            else:
                skipped += 1
        else:
            Picture.create(vals); created += 1
    else:
        # créer une image orpheline (model_id = False)
        Picture.create(vals); orphaned += 1

print(f"Done. total={total}, created={created}, updated={updated}, skipped={skipped}, orphaned={orphaned}")
