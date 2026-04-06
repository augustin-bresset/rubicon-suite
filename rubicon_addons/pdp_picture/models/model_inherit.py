# rubicon_addons/pdp_picture/models/model_inherit.py
from odoo import models, fields

class ProductModel(models.Model):
    _inherit = 'pdp.product.model'

    picture_image = fields.Image(compute='_compute_image', store=False)
    drawing_image = fields.Image(compute='_compute_image', store=False)
    drawing_filename = fields.Char(compute='_compute_image', store=False)

    def _compute_image(self):
        Pic = self.env['pdp.picture']
        Product = self.env['pdp.product']
        for rec in self:
            products = Product.search([('model_id', '=', rec.id)])
            pic = Pic.search([('scope', '=', 'model'), ('product_ids', 'in', products.ids)], limit=1) if products else Pic.browse()
            if pic:
                rec.picture_image = pic.image_1920
                rec.drawing_image = pic.drawing_1920
                rec.drawing_filename = pic.drawing_filename
            else:
                rec.picture_image = False
                rec.drawing_image = False
                rec.drawing_filename = False
