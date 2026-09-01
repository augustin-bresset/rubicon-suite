# rubicon_addons/pdp_picture/models/model_inherit.py
from odoo import models, fields


class ProductModel(models.Model):
    """Picture-related fields of a product model.

    Defined here, not in pdp_product: the base model must not reference
    pdp.picture, which belongs to this module (pdp_picture depends on
    pdp_product, not the other way round).
    """
    _inherit = 'pdp.product.model'

    picture_id = fields.Many2one(
        comodel_name='pdp.picture',
        compute='_compute_picture',
        string='Main Picture',
        store=False,
    )
    picture_image = fields.Image(compute='_compute_picture', store=False)
    drawing_image = fields.Image(compute='_compute_picture', store=False)
    drawing_filename = fields.Char(compute='_compute_picture', store=False)

    def _compute_picture(self):
        Pic = self.env['pdp.picture']
        Product = self.env['pdp.product']
        for rec in self:
            products = Product.search([('model_id', '=', rec.id)])
            pic = Pic.search(
                [('scope', '=', 'model'), ('product_ids', 'in', products.ids)],
                limit=1,
            ) if products else Pic.browse()
            rec.picture_id = pic
            rec.picture_image = pic.image_1920 if pic else False
            rec.drawing_image = pic.drawing_1920 if pic else False
            rec.drawing_filename = pic.drawing_filename if pic else False
