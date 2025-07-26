from odoo import models, fields

class ProductStone(models.Model):
    _name = 'pdp.product.stone'
    _description = 'Product Stone'

    product_code = fields.Many2one(
        comodel_name='pdp.product',
        string='Product Code',
        required=True,
        ondelete='cascade'
    )
    
    stone_code = fields.Many2one(
        comodel_name='pdp.stone',
        string='Stone Code',
        required=True
    )
    
    pieces = fields.Integer(
        string="Number of stones",
        required=True
    )
    
    weight = fields.Char(
        string="Weight of one stone",
        required=True
    )