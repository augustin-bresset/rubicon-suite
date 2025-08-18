# wizard/component_metal.py
from odoo import models, api

OZ_TO_G = 31.1034768

class PriceMetal(models.TransientModel):
    _name = 'pdp.price.metal'
    _description = 'Metal Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):

        if not product.model_id:
            return self._payload('metal', 0.0, 0.0, currency)

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}
        ModelMetal = self.env['pdp.product.model.metal'].with_context(clean_ctx)
        model_metal = ModelMetal.search([
            ('model_id', '=', product.model_id.id),
            ('metal_version', '=', product.metal),
        ], limit=1)
        if not model_metal:
            return self._payload('metal', 0.0, 0.0, currency)
        
        if margin:
            Marge = self.env['pdp.margin.metal'].with_context(clean_ctx)
            margin_id = Marge.search([
                ('margin_id', '=', margin.id),
                # ('metal_id', 'in', [k[0] for k in key_set]),
                ('metal_purity_id', '=', model_metal.purity_id.id),
            ], limit=1)
            
            rate = margin_id.rate or 1.0

        total_cost = total_margin = 0.0
            
        # Need USD for price computation
        try:
            usd = self.env.ref('base.USD')
        except Exception:
            usd = currency  # au pire aucune conversion

        # Exemple: cost_per_gram = cost_per_ounce / 31.1034768
        cost_per_gram_usd = (model_metal.metal_id.cost or 0.0) / OZ_TO_G
        grams = model_metal.weight or 0.0
        usd_cost = cost_per_gram_usd * grams
        total_cost = self._convert(usd_cost, usd, currency, date)
        if margin:
            total_margin += (rate - 1.0) * total_cost

        return self._payload('metal', total_cost, total_margin, currency)
