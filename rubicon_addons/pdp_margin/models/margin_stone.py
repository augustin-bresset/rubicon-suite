
from odoo import fields, models


class MarginStone(models.Model):
    _name="pdp.margin.stone"
    _description="Stone Margin"
    
    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True,
    )
    
    stone_type_id = fields.Many2one(
        string="Stone Type Code",
        comodel_name="pdp.stone.type",
        required=True,
        index=True
    )
    
    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
