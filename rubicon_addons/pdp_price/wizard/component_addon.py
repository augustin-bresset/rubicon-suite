from odoo import fields, models, api

class PriceAddon(models.TransientModel):
    _name="pdp.price.addon"
    _description="Compute Addon Price"
    _inherit="pdp.price.component"


    @api.model
    def compute(self, *, product, margin, currency, date):

        groups = self.env['pdp.addon.cost'].read_group(
            domain=[('product_id', '=', product.id)],
            fields=['cost:sum', 'currency_id', 'addon_id'],
            groupby=['addon_id', 'currency_id'],
        )
        
        margin_map = {}
        if margin and groups:
            addon_ids = [g['addon_id'][0] for g in groups if g.get('addon_id')]
            if addon_ids:
                ml = self.env['pdp.margin.addon'].search([
                    ('margin_id', '=', margin.id),
                    ('addon_id', 'in', addon_ids),
                ])
                margin_map = {r.addon_id.id: (r.rate or 1.0) for r in ml}

        total_cost = 0.0
        total_margin = 0.0

        for g in groups:
            sum_cost = g.get('cost_sum') or 0.0
            from_cur = g.get('currency_id') and self.env['res.currency'].browse(g['currency_id'][0]) or currency
            cost_in_cur = self._convert(sum_cost, from_cur, currency, date)

            total_cost += cost_in_cur

            addon_id = g.get('addon_id') and g['addon_id'][0]
            rate = margin_map.get(addon_id, 1.0)
            total_margin += (rate - 1.0) * cost_in_cur
        

        return self._payload('addon', total_cost, total_margin, currency)