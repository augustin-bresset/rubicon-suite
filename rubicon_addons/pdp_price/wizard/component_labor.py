from odoo import models, fields, api

class PriceLabor(models.TransientModel):
    _name = 'pdp.price.labor'
    _description = 'Labor Price Component'
    _inherit="pdp.price.component"



    @api.depends()
    def compute(self, *, product, margin, currency, date):

        groups = self.env['pdp.labor.cost'].read_group(
            domain=[('product', '=', product.id)],
            fields=['cost:sum', 'currency_id', 'labor_id'],
            groupby=['labor_id', 'currency_id'],
        )

        
        margin_map = {}
        if margin and groups:
            labor_ids = [g['labor_id'][0] for g in groups if g.get('labor_id')]
            if labor_ids:
                ml = self.env['pdp.margin.labor'].search([
                    ('margin_id', '=', margin.id),
                    ('labor_id', 'in', labor_ids),
                ])
                margin_map = {r.labor_id.id: (r.rate or 1.0) for r in ml}

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

            labor_id = g.get('labor_id') and g['labor_id'][0]
            rate = margin_map.get(labor_id, 1.0)
            total_margin += (rate - 1.0) * cost
        

        return self._payload('labor', total_cost, total_margin, currency)        