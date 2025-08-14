# wizard/component_stone.py
from odoo import models, api

class PriceStone(models.TransientModel):
    _name = 'pdp.price.stone'
    _description = 'Stone Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):
        total_cost = total_margin = 0.0

        lines = self.env['pdp.product.stone'].search([('product_id', '=', product.id)])
        for line in lines:
            cur = line.stone_id.currency_id or currency
            unit_cost = self._convert(line.stone_id.unit_cost or 0.0, cur, currency, date)
            cost = unit_cost * (line.pieces or 0.0)
            total_cost += cost

            rate = 1.0
            if margin:
                mline = self.env['pdp.margin.stone'].search([
                    ('margin_id', '=', margin.id),
                    ('stone_type_id', '=', line.stone_id.type_id.id),
                ], limit=1)
                rate = (mline.rate or 1.0) if mline else 1.0
            total_margin += (rate - 1.0) * cost

        return self._payload('stone', total_cost, total_margin, currency)
