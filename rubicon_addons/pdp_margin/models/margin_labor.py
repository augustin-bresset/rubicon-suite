from odoo import fields, models


class MarginLabor(models.Model):
    _name="pdp.margin.labor"
    _description="Labor Margin"
    
    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True
        )

    labor_id = fields.Many2one(
        comodel_name="pdp.labor.type",
        string="Labor Type",
        required=True,
        index=True
    )
    
    rate = fields.Float(
        string="Margin Labor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
    