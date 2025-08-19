
from odoo import fields, models


class MarginPart(models.Model):
    _name="pdp.margin.part"
    _description="Part Margin"
    
    
    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True
        )
    
    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
