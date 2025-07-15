from odoo import models, fields

class StoneShade(models.Model):
    _name = "pdp.stone.shade"
    _description = "Stone Shade"
    # _table = "stone_shades"
    # _auto  = False
    _rec_name = "shade"

    code  = fields.Char(string="Code", readonly=False)
    shade = fields.Char(string="Shade", readonly=False)