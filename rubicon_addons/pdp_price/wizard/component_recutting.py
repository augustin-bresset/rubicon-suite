from odoo import models, api

MIN_REC_WEIGHT = 0.4  # minimum recutting weight per stone (carats)


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
            effective_weight = max(MIN_REC_WEIGHT, rw)
            total_cost += converted_cost * effective_weight * (line.pieces or 1)

        return self._payload('recutting', total_cost, 0.0, currency)
