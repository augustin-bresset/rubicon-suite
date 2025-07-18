from odoo import models, fields

class StoneCategory(models.Model):
    _name = "pdp.stone.category"
    _description = "Stone Category"
    _rec_name = "code"

    code = fields.Char(string="Code", readonly=False)
    name = fields.Char(string="Name", readonly=False)

    type_codes = fields.One2many(
        comodel_name="pdp.stone.type",
        inverse_name="category_code",
        string="Types",
    )