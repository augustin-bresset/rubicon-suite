# Exécuté dans "odoo shell" → 'env' est dispo
models = [
    'pdp.stone.category','pdp.stone.type','pdp.stone.shape','pdp.stone.shade','pdp.stone.size','pdp.stone.weight','pdp.stone',
    'pdp.metal.purity','pdp.metal','pdp.part','pdp.part.cost',
    'pdp.product.category','pdp.product.model','pdp.product.model.matching','pdp.product.model.metal',
    'pdp.product.stone.composition','pdp.product','pdp.product.stone',
    'pdp.labor.type','pdp.addon.type','pdp.addon.cost','pdp.labor.cost.product','pdp.labor.cost.model',
    'pdp.margin','pdp.margin.labor','pdp.margin.stone','pdp.margin.metal','pdp.margin.addon',
]
for m in models:
    try:
        print(f"{m:35s} ->", env[m].sudo().search_count([]))
    except Exception as e:
        print(f"{m:35s} -> ERROR: {e}")
