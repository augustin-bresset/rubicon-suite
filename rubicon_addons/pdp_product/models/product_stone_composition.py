from odoo import models, fields

class ProductStoneComposition(models.Model):
    _name = 'pdp.product.stone.composition'
    _description = 'Group of stones used in a product (without metal)'
    _rec_name = 'code'

    code = fields.Char(string='Composition Code', required=True, index=True)
    
    stone_line_ids = fields.One2many(
        comodel_name='pdp.product.stone',
        inverse_name='composition_id',
        string='Stone Lines'
    )
