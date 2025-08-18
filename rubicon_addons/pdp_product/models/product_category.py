from odoo import models, fields

class ModelCategory(models.Model):
    _name = 'pdp.product.category'
    _description = 'Ornament Category'
    _rec_name = 'code'

    code = fields.Char(string='Category Code', required=True, index=True)
    name = fields.Char(string='Category Name', required=True)
    waste = fields.Float(
        string='Metal Waste (%)',
        digits=(3, 2),
        required=True
    )

    model_ids = fields.One2many(
        comodel_name="pdp.product.model",
        inverse_name="category_id",
        string="Models",
    )

