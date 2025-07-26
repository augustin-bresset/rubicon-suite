from odoo import models, fields

class ProductPart(models.Model):
    _name = 'pdp.product.part'
    _description = 'Product Part'

    product_code = fields.Many2one(
        comodel_name="pdp.product",
        required=True
    )
    
    part_code = fields.Many2one(
        comodel_name="pdp.part",
        required=True
    )

    quantity = fields.Integer()
    
    
    