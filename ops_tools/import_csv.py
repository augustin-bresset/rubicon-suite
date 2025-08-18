import sys
import os
from odoo.addons.rubicon_import.import_scripts.generic import import_csv

# what = os.getenv("WHAT", "all").lower()
what = "all"
everything = what == "all"

print(f"[INFO] IMPORT {what.upper()}")

# STONE
if everything or "stone" in sys.argv:
    import_csv(env, env['pdp.stone.category'], 'pdp_stone')
    import_csv(env, env['pdp.stone.type'], 'pdp_stone')
    import_csv(env, env['pdp.stone.shape'], 'pdp_stone')
    import_csv(env, env['pdp.stone.shade'], 'pdp_stone')
    import_csv(env, env['pdp.stone.size'], 'pdp_stone')
    import_csv(env, env['pdp.stone.weight'], 'pdp_stone')
    import_csv(env, env['pdp.stone'], 'pdp_stone')

    
# METAL
if everything or "metal" in sys.argv:

    import_csv(env, env['pdp.metal.purity'], 'pdp_metal')
    import_csv(env, env['pdp.metal'], 'pdp_metal')

    ## Part
    import_csv(env, env['pdp.part'], 'pdp_metal')
    import_csv(env, env['pdp.part.cost'], 'pdp_metal')


# PRODUCT
if everything or "product" in sys.argv:

    import_csv(env, env['pdp.product.category'], 'pdp_product')
    import_csv(env, env['pdp.product.model'], 'pdp_product', fields_maj=['parent_model_id'])

    import_csv(env, env['pdp.product.model.matching'], 'pdp_product')
    import_csv(env, env['pdp.product.model.metal'], 'pdp_product')

    import_csv(env, env['pdp.product.stone.composition'], 'pdp_product')

    import_csv(env, env['pdp.product'], 'pdp_product')

    from odoo.addons.rubicon_import.import_scripts.update import update_from_csv
    import re


    update_from_csv(
        env,
        env['pdp.stone.size'],
        datafile_path='pdp_product/data/pdp.product.stone.csv',
        mapping={"reshaped_size_id" : "name"},
        match_field='name',  
    )
    update_from_csv(
        env,
        env['pdp.stone.size'],
        datafile_path='pdp_product/data/pdp.product.stone.csv',
        mapping={"stone_size" : "name"},
        match_field='name',  
    )

    stone_mapping = {
        "stone_id"     : "code",
        "stone_type"   : "type_id",
        "stone_shade"  : "shade_id",
        "stone_shape"  : "shape_id",
        "stone_size"   : "size_id",
    }

    update_from_csv(
        env,
        env['pdp.stone'],
        datafile_path='pdp_product/data/pdp.product.stone.csv',
        mapping=stone_mapping,
        match_field='code',  
    )

    import_csv(env, env['pdp.product.stone'], 'pdp_product')

# Labor
if everything or "labor" in sys.argv:

    import_csv(env, env['pdp.labor.type'], 'pdp_labor')
    import_csv(env, env['pdp.addon.type'], 'pdp_labor')

    import_csv(env, env['pdp.addon.cost'], 'pdp_labor')
    import_csv(env, env['pdp.labor.cost.product'], 'pdp_labor')
    import_csv(env, env['pdp.labor.cost.model'], 'pdp_labor')


# Margin
if everything or "margin" in sys.argv:

    import_csv(env, env['pdp.margin'], 'pdp_margin')
    import_csv(env, env['pdp.margin.labor'], 'pdp_margin')
    import_csv(env, env['pdp.margin.stone'], 'pdp_margin')
    import_csv(env, env['pdp.margin.metal'], 'pdp_margin')
    import_csv(env, env['pdp.margin.addon'], 'pdp_margin')

env.cr.commit()