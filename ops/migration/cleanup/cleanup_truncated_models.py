# Repair pdp.product.model records whose code was truncated at import
# (e.g. a model 'P' carrying the product 'P1009-GA+RHO+DIO/W').
#
# Rules:
# - A product whose code prefix (before '-') differs from its model's code
#   is relinked to the model matching that prefix (created if missing).
# - A model left with no product, no metal weight and no labor cost is
#   deleted when it was a relink source, or when its short code is a
#   strict prefix of another model's code (import artifacts like 'B1', 'R').
#
# Run with:
#   docker compose exec -T odoo odoo shell -d rubicon --http-port=8073 \
#       < ops/migration/cleanup/cleanup_truncated_models.py

Model = env['pdp.product.model']  # noqa: F821 (odoo shell provides env)
Product = env['pdp.product']  # noqa: F821
LaborCost = env['pdp.labor.cost.model']  # noqa: F821

relinked = []
sources = set()
for product in Product.with_context(active_test=False).search([]):
    model = product.model_id
    if not model:
        continue
    prefix = (product.code or '').split('-')[0].strip()
    if not prefix or prefix == model.code:
        continue
    target = Model.search([('code', '=', prefix)], limit=1)
    if not target:
        target = Model.create({
            'code': prefix,
            'category_id': model.category_id.id if model.category_id else False,
        })
    product.model_id = target
    sources.add(model.id)
    relinked.append((product.code, model.code, prefix))

all_codes = Model.search([]).mapped('code')
deleted = []
for model in Model.search([]):
    if Product.with_context(active_test=False).search_count(
            [('model_id', '=', model.id)]):
        continue
    if model.metal_weights_ids or LaborCost.search_count(
            [('model_id', '=', model.id)]):
        continue
    is_source = model.id in sources
    is_prefix_artifact = len(model.code or '') <= 2 and any(
        c != model.code and c.startswith(model.code) for c in all_codes)
    if is_source or is_prefix_artifact:
        deleted.append(model.code)
        model.unlink()

print('Relinked %d products:' % len(relinked))
for code, old, new in relinked:
    print('  %-30s %s -> %s' % (code, old, new))
print('Deleted %d empty truncated models: %s' % (len(deleted), deleted))
env.cr.commit()  # noqa: F821
print('committed')
