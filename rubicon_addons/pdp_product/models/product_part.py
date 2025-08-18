from odoo import models, fields

class ProductPart(models.Model):
    _name = 'pdp.product.part'
    _description = 'Product Part'

    product_id = fields.Many2one(
        comodel_name="pdp.product",
        required=True,
        index=True
    )
    
    part_id = fields.Many2one(
        comodel_name="pdp.part",
        required=True
    )

    quantity = fields.Integer()
    
    
    