
from odoo import fields, models


class MarginMetal(models.Model):
    _name="pdp.margin.metal"
    _description="Metal Margin"
    
    
    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True
        )
    
    metal_purity_id = fields.Many2one(
        string="Metal Purity",
        comodel_name="pdp.metal.purity",
        required=True,
        index=True
        )
    
    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
