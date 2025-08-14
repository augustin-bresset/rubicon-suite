
from odoo import fields, models


class MarginMetal(models.Model):
    _name="pdp.margin.metal"
    _description="Metal Margin"
    
    
    margin = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        )
    
    metal_purity = fields.Many2one(
        string="Metal Purity",
        comodel_name="pdp.metal.purity",
        required=True
        )
    
    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
