

## Usecase

### Stone
Create Stone Tables and Import from CSV

#### Create data
```sh
python3 -m rubicon_import.raw_to_data.raw_to_data_stone
```
This command will convert the data from raw into a good format for odoo

#### Create Table
```sh
docker compose exec odoo odoo -d rubicon -i pdp_stone --stop-after-init
``` 
Create the table from the models of the module


#### Import Data
Finally in the (python) shell
```sh
docker compose exec odoo odoo shell -d rubicon
```

Launch the imports scripts 
```py
from odoo.addons.rubicon_import.import_scripts.generic import import_csv

# STONE
import_csv(env, env['pdp.stone.category'], 'pdp_stone')
import_csv(env, env['pdp.stone.type'], 'pdp_stone')
import_csv(env, env['pdp.stone.shape'], 'pdp_stone')
import_csv(env, env['pdp.stone.shade'], 'pdp_stone')
import_csv(env, env['pdp.stone.size'], 'pdp_stone')
import_csv(env, env['pdp.stone.weight'], 'pdp_stone')
import_csv(env, env['pdp.stone'], 'pdp_stone')

env.cr.commit()
```





```py

from odoo.addons.rubicon_import.import_scripts.generic import import_csv

# STONE
import_csv(env, env['pdp.stone.category'], 'pdp_stone')
import_csv(env, env['pdp.stone.type'], 'pdp_stone')
import_csv(env, env['pdp.stone.shape'], 'pdp_stone')
import_csv(env, env['pdp.stone.shade'], 'pdp_stone')
import_csv(env, env['pdp.stone.size'], 'pdp_stone')
import_csv(env, env['pdp.stone.weight'], 'pdp_stone')
import_csv(env, env['pdp.stone'], 'pdp_stone')


# METAL
import_csv(env, env['pdp.metal.purity'], 'pdp_metal')
import_csv(env, env['pdp.metal'], 'pdp_metal')

## Part
import_csv(env, env['pdp.part'], 'pdp_metal')
import_csv(env, env['pdp.part.cost'], 'pdp_metal')


# PRODUCT
import_csv(env, env['pdp.product.category'], 'pdp_product')
import_csv(env, env['pdp.product.model'], 'pdp_product', fields_maj=['parent_model'])

import_csv(env, env['pdp.product.model.matching'], 'pdp_product')
import_csv(env, env['pdp.product.model.metal'], 'pdp_product')

import_csv(env, env['pdp.product.stone.composition'], 'pdp_product')

import_csv(env, env['pdp.product'], 'pdp_product')

from odoo.addons.rubicon_import.import_scripts.update import update_from_csv
import re

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
    "stone"        : "code",
    "stone_type"   : "type",
    "stone_shade"  : "shade",
    "stone_shape"  : "shape",
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

# Labor
import_csv(env, env['pdp.labor.type'], 'pdp_labor')
import_csv(env, env['pdp.addon.type'], 'pdp_labor')

import_csv(env, env['pdp.addon.cost'], 'pdp_labor')
import_csv(env, env['pdp.labor.cost.product'], 'pdp_labor')
import_csv(env, env['pdp.labor.cost.model'], 'pdp_labor')


# Margin

import_csv(env, env['pdp.margin'], 'pdp_margin')
import_csv(env, env['pdp.margin.labor'], 'pdp_margin')
import_csv(env, env['pdp.margin.stone'], 'pdp_margin')
import_csv(env, env['pdp.margin.metal'], 'pdp_margin')
import_csv(env, env['pdp.margin.addon'], 'pdp_margin')

env.cr.rollback()
```

