from odoo import models, fields, api

class PricePart(models.TransientModel):
    _name = 'pdp.price.part'
    _description = 'Part Price Component'
    _inherit = 'pdp.price.component' 



    @api.depends()
    def compute(self, *, product, margin, currency, date):
        
        groups = self.env['pdp.part.cost'].read_group(
            domain=[('product_code', '=', product.id)],
            fields=['cost:sum', 'currency_id', 'part_id'],
            groupby=['currency_id', 'part_id'],
        )
        
        margin_map = {}
        if margin and groups:
            part_ids = [g['part_id'][0] for g in groups if g.get('part_id')]
            if part_ids:
                ml = self.env['pdp.margin.part'].search([
                    ('margin_id', '=', margin.id),
                    ('part_id', 'in', part_ids),
                ])
                margin_map = {r.part_id.id: (r.rate or 1.0) for r in ml}

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

            part_id = g.get('part_id') and g['part_id'][0]
            rate = margin_map.get(part_id, 1.0)
            total_margin += (rate - 1.0) * cost
        

        return self._payload('part', total_cost, total_margin, currency)        