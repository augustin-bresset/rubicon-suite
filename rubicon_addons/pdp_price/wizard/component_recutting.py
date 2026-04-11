from odoo import models, api


class PriceRecutting(models.TransientModel):
    _name = 'pdp.price.recutting'
    _description = 'Recutting Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):
        if not product.stone_composition_id:
            return self._payload('recutting', 0.0, 0.0, currency)

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        lines = self.env['pdp.product.stone'].with_context(clean_ctx).search([
            ('composition_id', '=', product.stone_composition_id.id)
        ])
        if not lines:
            return self._payload('recutting', 0.0, 0.0, currency)

        # Pre-fetch category chain to avoid N+1
        lines.mapped('stone_id.type_id.category_id')

        total_cost = 0.0
        for line in lines:
            stone = line.stone_id
            if not stone or not stone.type_id or not stone.type_id.category_id:
                continue
            cat = stone.type_id.category_id
            unit_cost = cat.recutting_cost or 0.0
            if unit_cost <= 0.0:
                continue
            from_cur = cat.recutting_currency_id or currency
            weight = line.weight or 0.0
            pieces = line.pieces or 1
            total_cost += self._convert(unit_cost, from_cur, currency, date) * weight * pieces

        return self._payload('recutting', total_cost, 0.0, currency)
