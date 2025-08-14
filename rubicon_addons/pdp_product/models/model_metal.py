from odoo import models, fields

class ModelMetal(models.Model):
    _name = 'pdp.product.model.metal'
    _description = 'Model Metal with quantity'

    
    weight = fields.Float(
        string='Weight in reference Metal (g)',
        digits=(6, 3),
        required=True
    )
    
    metal_version = fields.Char(
        string="Version of Metal (W, W2, ...)",
        required=True
        )
    
    metal  = fields.Many2one(
        comodel_name='pdp.metal',
        string='Metal Code'
    )
    
    purity  = fields.Many2one(
        comodel_name='pdp.metal.purity',
        string='Metal Purity'
    )

    model = fields.Many2one(
        'pdp.product.model', 
        required=True, ondelete='cascade')

    