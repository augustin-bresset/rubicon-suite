from odoo import models, fields

class StoneCategory(models.Model):
    _name = "pdp.stone.category"
    _description = "Stone Category"
    _rec_name = "code"

    code = fields.Char(string="Code", required=True, index=True)
    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=True)

    recutting_cost = fields.Monetary(
        string='Recutting Cost /ct',
        currency_field='recutting_currency_id',
        default=0.0,
        help='Recutting cost per carat for stones of this category.',
    )
    recutting_currency_id = fields.Many2one(
        'res.currency',
        string='Recutting Currency',
    )

    type_ids = fields.One2many(
        comodel_name="pdp.stone.type",
        inverse_name="category_id",
        string="Types",
    )
    _sql_constraints = [("name_uniq","unique(name)","Category must be unique.")]
