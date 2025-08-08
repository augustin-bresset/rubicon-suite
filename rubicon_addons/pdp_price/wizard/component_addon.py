from odoo import fields, models, api

class PriceAddon(models.TransientModel):
    _name="pdp.price.addon"
    _description="Compute Addon Price"
    _inherit="pdp.price.component"


    @api.model
    def compute(self, *, product_code, margin_code=None, currency, date):
        cost = 0.0
        margin = 0.0
        
        groups = self.env['pdp.addon.cost'].read_group(
            domain=[('product_code', '=', product_code.id)],
            fields=['cost:sum', 'currency'],
            groupby=['currency'],
        )
        
        margin_map = {}
        if margin and groups:
            addon_ids = [g['addon_id'][0] for g in groups if g.get('addon_id')]
            if addon_ids:
                ml = self.env['pdp.margin.addon'].search([
                    ('margin_id', '=', margin_code.id),
                    ('addon_id', 'in', addon_ids),
                ])
                margin_map = {r.addon_id.id: (r.rate or 1.0) for r in ml}

        total_cost = 0.0
        total_margin = 0.0

        for g in groups:
            sum_cost = g.get('cost_sum') or 0.0
            if g.get('currency_id'):
                from_cur = self.env['res.currency'].browse(g['currency_id'][0])
            else:
                from_cur = currency

            cost = self._convert(sum_cost, from_cur, currency, date)
            total_cost += cost

            addon_id = g.get('addon_id') and g['addon_id'][0]
            rate = margin_map.get(addon_id, 1.0)
            total_margin += (rate - 1.0) * cost
        

        return self.compute_payload('addon', total_cost, total_margin, currency)