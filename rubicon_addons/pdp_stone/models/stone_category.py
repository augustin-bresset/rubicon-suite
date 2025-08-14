from odoo import models, fields

class StoneCategory(models.Model):
    _name = "pdp.stone.category"
    _description = "Stone Category"
    _rec_name = "code"

    code = fields.Char(string="Code", required=True, index=True)
    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=True)

    type_ids = fields.One2many(
        comodel_name="pdp.stone.type",
        inverse_name="category_id",
        string="Types",
    )
    _sql_constraints = [("name_uniq","unique(name)","Category must be unique.")]
