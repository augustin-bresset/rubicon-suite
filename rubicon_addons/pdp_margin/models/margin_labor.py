from odoo import fields, models


class MarginLabor(models.Model):
    _name="pdp.margin.labor"
    _description="Labor Margin"
    
    margin_code = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True
        )

    margin_parts = fields.Float(digits=(5, 3))
    margin_stone = fields.Float(digits=(5, 3))
    margin_metal = fields.Float(digits=(5, 3))
    

    