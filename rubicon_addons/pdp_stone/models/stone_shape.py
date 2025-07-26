from odoo import models, fields

class StoneShape(models.Model):
    _name = "pdp.stone.shape"
    _description = "Stone Shape"

    _rec_name = "code"

    code  = fields.Char(string="Code", required=True, size=5)
    shape = fields.Char(string="Shape", required=True)

