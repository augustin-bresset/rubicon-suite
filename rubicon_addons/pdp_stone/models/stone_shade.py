from odoo import models, fields

class StoneShade(models.Model):
    _name = "pdp.stone.shade"
    _description = "Stone Shade"

    _rec_name = "code"

    code  = fields.Char(string="Code", required=True, size=5)
    shade = fields.Char(string="Shade", required=True)