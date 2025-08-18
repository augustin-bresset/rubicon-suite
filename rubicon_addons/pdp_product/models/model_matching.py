from odoo import models, fields

class MatchingModel(models.Model):
    _name = 'pdp.product.model.matching'
    _description = 'Matching Between Two Models'

    model_one_id = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Model One',
        index=True,
    )
    model_two_id = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Model Two',
        index=True,
    )
