from odoo import fields, models

class PriceComponent(models.Model):
    _name = 'pdp.price.product'

    _sql_constraints = [
        ('uniq_product',
         'unique(product_code)',
         'Uniq price per product'),
    ]
    
    product_code = fields.Many2one(
        'pdp.product',
        string='Product',
        required=True,
        ondelete='cascade'
    )
    margin_code = fields.Many2one(
        'pdp.margin',
        string='Margin'
    )

    date = fields.Date(required=True, default=fields.Date.context_today)    
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    @api.depends('margin_code', 'currency_id')
    def _compute_totals(self):
        for rec in self:
            comps = [
                rec.component_stone_id, rec.component_metal_id,
                rec.component_labor_id, rec.component_addon_id, rec.component_part_id
            ]
            total_cost = sum((c.cost or 0.0) for c in comps if c)
            total_margin = sum((c.margin or 0.0) for c in comps if c)
            rec.cost = rec.currency_id.round(total_cost)
            rec.margin = rec.currency_id.round(total_margin)
            rec.price = rec.cost + rec.margin
            
            