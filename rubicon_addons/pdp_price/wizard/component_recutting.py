from odoo import models, api


class PriceRecutting(models.TransientModel):
    _name = 'pdp.price.recutting'
    _description = 'Recutting Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):
        if not product.stone_composition_id:
            return self._payload('recutting', 0.0, 0.0, currency)

        config = self.env['pdp.stone.recutting.config'].get_config()
        unit_cost = config.cost or 0.0
        min_weight = config.min_weight or 0.0
        if unit_cost <= 0.0:
            return self._payload('recutting', 0.0, 0.0, currency)

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        lines = self.env['pdp.product.stone'].with_context(clean_ctx).search([
            ('composition_id', '=', product.stone_composition_id.id)
        ])
        if not lines:
            return self._payload('recutting', 0.0, 0.0, currency)

        from_cur = config.currency_id or currency
        converted_cost = self._convert(unit_cost, from_cur, currency, date)

        total_cost = 0.0
        for line in lines:
            rw = line.reshaped_weight or 0.0
            if rw <= 0.0:
                continue
            # Charge the reshaped weight, with a configurable per-stone minimum
            # (a small stone still costs the same to recut).
            effective_weight = max(min_weight, rw)
            total_cost += converted_cost * effective_weight * (line.pieces or 1)

        # Recutting (REC) is stone labor, so it carries the stone-labor margin,
        # the same rate the setting line uses.
        stone_rate = (margin.labor_stone_rate or 1.0) if margin else 1.0
        total_margin = (stone_rate - 1.0) * total_cost
        return self._payload('recutting', total_cost, total_margin, currency)
