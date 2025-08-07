
from odoo import fields, models


class MarginStone(models.Model):
    _name="pdp.margin.stone"
    _description="Stone Margin"
    
    margin_code = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True
    )
    
    stone_type_code = fields.Many2one(
        string="Stone Type Code",
        comodel_name="pdp.stone.type",
        required=True
    )
    
    margin = fields.Float(
        string="Margin",
        digits=(5, 3),
        required=True,
    )
