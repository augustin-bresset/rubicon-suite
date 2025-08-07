
from odoo import fields, models


class MarginMetal(models.Model):
    _name="pdp.margin.metal"
    _description="Metal Margin"
    
    
    margin_code = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True
        )
    
    metal_purity_code = fields.Many2one(
        string="Metal Purity",
        comodel_name="pdp.metal.purity",
        required=True
        )
    
    margin = fields.Float(
        string="Margin",
        digits=(5, 3),
        required=True,
    )
