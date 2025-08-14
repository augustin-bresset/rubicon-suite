# wizard/component_metal.py
from odoo import models, api

class PriceMetal(models.TransientModel):
    _name = 'pdp.price.metal'
    _description = 'Metal Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):
        rels = self.env['pdp.product.model.metal'].search([('model_id', '=', product.model_id.id)])
        usd = self.env.ref('base.USD')  

        total_cost = total_margin = 0.0
        for rel in rels:
            metal = rel.metal_id  # pdp.metal
            # Exemple: cost_per_gram = cost_per_ounce / 31.1034768
            cost_per_gram_usd = (metal.cost_per_ounce or 0.0) / 31.1034768
            # Poids converti selon pureté/conversion pondérale si besoin
            grams = rel.weight_grams or 0.0
            usd_cost = cost_per_gram_usd * grams
            cost = self._convert(usd_cost, usd, currency, date)
            total_cost += cost

            rate = 1.0
            if margin:
                # Ex: marge par pureté / métal
                mline = self.env['pdp.margin.metal'].search([
                    ('margin_id', '=', margin.id),
                    ('metal_id', '=', metal.id),
                    ('purity_id', '=', rel.purity_id.id),
                ], limit=1)
                rate = (mline.rate or 1.0) if mline else 1.0

            total_margin += (rate - 1.0) * cost

        return self._payload('metal', total_cost, total_margin, currency)
