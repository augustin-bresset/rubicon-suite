from odoo import models, fields

class ProductStone(models.Model):
    _name = 'pdp.product.stone'
    _description = 'Product Stone'

    stone_id = fields.Many2one(
        comodel_name='pdp.stone',
        string='Stone Code Buyed',
        required=True,
        index=True
    )
    
    pieces = fields.Integer(
        string="Number of stones",
        required=True,
        default=1
    )
    
    weight = fields.Char(
        string="Weight of one stone buyed",
    )

    reshaped_shape_id = fields.Many2one(
        comodel_name='pdp.stone.shape',
        string='Shape of Stone Reshaped',
    )
    
    reshaped_size_id  = fields.Many2one(
        comodel_name='pdp.stone.size',
        string='Size of Stone Code Reshaped for product',
    )
    
    reshaped_weight = fields.Char(
        string="Weight of one stone used",   
    )
    
    composition_id = fields.Many2one(
        comodel_name='pdp.product.stone.composition',
        string='Composition',
        required=True,
        ondelete='cascade'
    )