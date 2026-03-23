def post_init_hook(env):
    # Remove all PDP product models (cascade removes products, metal weights, model-level labor costs)
    env['pdp.product.model'].search([]).unlink()

    # Remove all SIS documents (cascade removes document line items)
    env['sis.document'].search([]).unlink()

    # Remove all SIS parties (res.partner records with a sis_code)
    env['res.partner'].search([('sis_code', '!=', False)]).unlink()

    # Remove all PDP margin records
    env['pdp.margin'].search([]).unlink()
