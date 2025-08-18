# Exécuté dans "odoo shell" → 'env' est dispo
models = [
    'pdp.stone.category','pdp.stone.type','pdp.stone.shape','pdp.stone.shade','pdp.stone.size','pdp.stone.weight','pdp.stone',
    'pdp.metal.purity','pdp.metal','pdp.part','pdp.part.cost',
    'pdp.product.category','pdp.product.model','pdp.product.model.matching','pdp.product.model.metal',
    'pdp.product.stone.composition','pdp.product','pdp.product.stone',
    'pdp.labor.type','pdp.addon.type','pdp.addon.cost','pdp.labor.cost.product','pdp.labor.cost.model',
    'pdp.margin','pdp.margin.labor','pdp.margin.stone','pdp.margin.metal','pdp.margin.addon',
]

import sys
m = sys.argv[1]
if not m in models:
    raise NameError(f"{m} is not a model valid.")

try:
    # Complete here
    ...
except Exception as e:
    print(f"{m:35s} -> ERROR: {e}")
