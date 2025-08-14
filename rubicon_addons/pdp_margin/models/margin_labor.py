from odoo import fields, models


class MarginLabor(models.Model):
    _name="pdp.margin.labor"
    _description="Labor Margin"
    
    margin = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True
        )

    rate_parts = fields.Float(
        string="Margin Parts Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
    
    rate_stone = fields.Float(
        string="Margin Stone Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
        
    rate_metal = fields.Float(
        string="Margin Metal Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )