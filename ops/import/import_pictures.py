"""
Import pictures; create/update when model exists,
otherwise create an orphan picture (model_id = False).
Run with: docker compose exec -T odoo odoo shell -d <DB> < ops/import/import_picture.py
"""
import base64
import binascii
import hashlib
import io
import os
import re
import traceback

from odoo.exceptions import UserError

# Garde-fous
if 'pdp.picture' not in env.registry.models:
    raise RuntimeError("Module pdp_picture non installé.")

Picture = env['pdp.picture']
Model = env['pdp.product.model']

base_path = '/mnt/extra-addons/pictures'
if not os.path.isdir(base_path):
    raise RuntimeError(f"Dossier introuvable: {base_path}")

pat = re.compile(r'^(?P<code>[^.]+)\.(jpg|jpeg|png)$', re.I)

created = updated = skipped = orphaned = errors = 0
total = 0

BATCH_SIZE = int(os.environ.get("PICTURE_IMPORT_BATCH", "25"))
CHUNK_SIZE = int(os.environ.get("PICTURE_IMPORT_CHUNK", str(3 * 1024 * 1024)))


def commit_batch(processed):
    if not processed:
        return

    env.cr.commit()
    env.clear()
    print(f"💾  committed batch of {processed} pictures")


def iter_base64(path, chunk_size):
    """Return (base64_bytes, md5_hexdigest) without loading the whole file."""

    digest = hashlib.md5()
    buffer = io.BytesIO()
    remainder = b""

    with open(path, "rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break

            digest.update(chunk)

            if remainder:
                chunk = remainder + chunk
                remainder = b""

            # keep a tail that is not a multiple of 3 for the next iteration
            length = (len(chunk) // 3) * 3
            if length:
                buffer.write(base64.b64encode(chunk[:length]))
                remainder = chunk[length:]
            else:
                remainder = chunk

        if remainder:
            buffer.write(base64.b64encode(remainder))

    return buffer.getvalue(), digest.hexdigest()

batch_count = 0

for fname in sorted(os.listdir(base_path)):
    m = pat.match(fname)
    if not m:
        continue
    total += 1

    code = (m.group('code') or '').upper()
    full = os.path.join(base_path, fname)

    try:
        b64, chk = iter_base64(full, CHUNK_SIZE)
    except (OSError, MemoryError, binascii.Error) as exc:
        skipped += 1
        errors += 1
        print(f"⚠️  {fname}: import failed ({exc.__class__.__name__}: {exc})")
        traceback.print_exc()
        continue

    # ✅ utiliser la bonne clé: 'code' (pas 'name')
    model = Model.search([('code', '=', code)], limit=1)

    vals = {
        'model_id': model.id if model else False,   # ← orphelin si pas de modèle
        'filename': fname,
        'image': b64,
        'checksum': chk,
    }

    try:
        with env.cr.savepoint():
            if model:
                pic = Picture.search([('model_id', '=', model.id)], limit=1)
                if pic:
                    if pic.checksum != chk:
                        pic.write(vals)
                        updated += 1
                    else:
                        skipped += 1
                else:
                    Picture.create(vals)
                    created += 1
            else:
                # créer une image orpheline (model_id = False)
                Picture.create(vals)
                orphaned += 1
    except UserError as exc:
        skipped += 1
        errors += 1
        try:
            message = str(exc)
        except Exception:
            message = repr(exc)
        print(f"⚠️  {fname}: import failed ({exc.__class__.__name__}: {message})")
        traceback.print_exc()
        env.clear()
        continue

    batch_count += 1
    if BATCH_SIZE and batch_count >= BATCH_SIZE:
        commit_batch(batch_count)
        batch_count = 0

if batch_count:
    commit_batch(batch_count)

print(
    "Done. total={total}, created={created}, updated={updated}, skipped={skipped}, "
    "orphaned={orphaned}, errors={errors}".format(
        total=total,
        created=created,
        updated=updated,
        skipped=skipped,
        orphaned=orphaned,
        errors=errors,
    )
)