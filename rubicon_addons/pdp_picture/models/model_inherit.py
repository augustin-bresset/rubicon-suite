# rubicon_addons/pdp_picture/models/model_inherit.py
from odoo import models, fields

class ProductModel(models.Model):
    _inherit = 'pdp.product.model'

    
    picture = fields.Image(compute='_compute_picture_image', store=False)

    def _compute_image(self):
        Pic = self.env['pdp.picture']
        for rec in self:
            pic = Pic.search([('model_id', '=', rec.id)], limit=1)
            rec.picture_image = pic.image if pic else False
            
            
