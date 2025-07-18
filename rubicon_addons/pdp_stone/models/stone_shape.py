from odoo import models, fields

class StoneShape(models.Model):
    _name = "pdp.stone.shape"
    _description = "Stone Shape"
    # _table = "stone_shapes"
    # _auto  = False
    _rec_name = "code"

    code  = fields.Char(string="Code", readonly=False)
    shape = fields.Char(string="Shape", readonly=False)

