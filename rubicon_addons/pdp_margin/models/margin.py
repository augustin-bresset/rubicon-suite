from odoo import fields, models


class Margin(models.Model):
    _name = "pdp.margin"
    _description = "Margin Name"
    _rec_name = "code"

    code = fields.Char(string="Margin Code", required=True, index=True)
    name = fields.Char(string="Margin Name", required=True)
    labor_metal_rate = fields.Float(
        string="Metal Labor Rate",
        digits=(5, 3),
        default=1.0,
    )
    labor_stone_rate = fields.Float(
        string="Stone Labor Rate",
        digits=(5, 3),
        default=1.0,
    )
