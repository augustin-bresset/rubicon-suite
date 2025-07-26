from odoo import models, fields

class StoneCategory(models.Model):
    _name = "pdp.stone.category"
    _description = "Stone Category"
    _rec_name = "code"

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", required=True)

    type_codes = fields.One2many(
        comodel_name="pdp.stone.type",
        inverse_name="category_code",
        string="Types",
    )