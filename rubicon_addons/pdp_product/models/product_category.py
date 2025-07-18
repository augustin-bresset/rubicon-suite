from odoo import models, fields

class ModelCategory(models.Model):
    _name = 'pdp.product.category'
    _description = 'Ornament Category'
    _rec_name = 'code'

    code = fields.Char(string='Category Code', required=True, size=2)
    name = fields.Char(string='Category Name', required=True, size=50)
    waste = fields.Float(
        string='Metal Waste (%)',
        digits=(3, 2),
        required=True
    )

    model_codes = fields.One2many(
        comodel_name="pdp.product.model",
        inverse_name="category_code",
        string="Models",
    )

