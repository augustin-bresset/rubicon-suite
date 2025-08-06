

## Usecase
```py

from odoo.addons.rubicon_import.import_scripts.generic import import_csv

import_csv(env, env['pdp.stone.category'], 'pdp_stone')
import_csv(env, env['pdp.stone.type'], 'pdp_stone')
import_csv(env, env['pdp.stone.shape'], 'pdp_stone')
import_csv(env, env['pdp.stone.shade'], 'pdp_stone')
import_csv(env, env['pdp.stone.size'], 'pdp_stone')
import_csv(env, env['pdp.stone.weight'], 'pdp_stone')
import_csv(env, env['pdp.stone'], 'pdp_stone')

import_csv(env, env['pdp.metal.purity'], 'pdp_metal')
import_csv(env, env['pdp.metal'], 'pdp_metal')

import_csv(env, env['pdp.part'], 'pdp_metal')
import_csv(env, env['pdp.part.cost'], 'pdp_metal')

import_csv(env, env['pdp.product.category'], 'pdp_product')
import_csv(env, env['pdp.product.model'], 'pdp_product', fields_maj=['parent_model_code'])

import_csv(env, env['pdp.product.model.matching'], 'pdp_product')
import_csv(env, env['pdp.product.model.metal'], 'pdp_product')

import_csv(env, env['pdp.product.stone.composition'], 'pdp_product')
import_csv(env, env['pdp.product'], 'pdp_product')

from odoo.addons.rubicon_import.import_scripts.update import update_from_csv

update_from_csv(
    env,
    model=env['pdp.stone.size'],
    datafile_path='pdp_product/data/pdp.product.stone.csv',
    mapping={"stone_size": "size"},
    match_field="size",
    filter = {'size': lambda s: re.sub(r"[A-WY-Z ]", "", s.upper())}
)

update_from_csv(
    env,
    env['pdp.stone.size'],
    datafile_path='pdp_product/data/pdp.product.stone.csv',
    mapping={"reshaped_size" : "size"},
    match_field='size',  
    filter = {'size': lambda s: re.sub(r"[A-WY-Z ]", "", s.upper())}
)

stone_mapping = {
    "stone_code"        : "code",
    "stone_type_code"   : "type_code",
    "stone_shade_code"  : "shade_code",
    "stone_shape_code"  : "shape_code",
    "stone_size"        : "size",
}

update_from_csv(
    env,
    env['pdp.stone'],
    datafile_path='pdp_product/data/pdp.product.stone.csv',
    mapping=stone_mapping,
    match_field='code',  
    filter = {'size': lambda s: re.sub(r"[A-WY-Z ]", "", s.upper())}
)

import_csv(env, env['pdp.product.stone'], 'pdp_product')



import_csv(env, env['pdp.labor.type'], 'pdp_labor')
import_csv(env, env['pdp.addon.type'], 'pdp_labor')

import_csv(env, env['pdp.addon.cost'], 'pdp_labor')
import_csv(env, env['pdp.labor.cost.product'], 'pdp_labor')
import_csv(env, env['pdp.labor.cost.model'], 'pdp_labor')

env.cr.rollback()

```

