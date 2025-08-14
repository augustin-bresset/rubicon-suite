from odoo import models, fields

class MatchingModel(models.Model):
    _name = 'pdp.product.model.matching'
    _description = 'Matching Between Two Models'

    model_one = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Model One',
    )
    model_two = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Model Two',
    )
