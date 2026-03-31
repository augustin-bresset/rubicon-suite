from odoo import models, fields

class PDPPictureTestWizard(models.TransientModel):
    _name = 'pdp.picture.test.wizard'
    _description = 'Test PDP Picture'

    model_id = fields.Many2one('pdp.product.model', string='Model', required=True)
    # on lit l’image si une photo existe pour ce modèle
    picture_id = fields.Many2one('pdp.picture', compute='_compute_picture', store=False)
    image = fields.Image(related='picture_id.image', readonly=True)
    filename = fields.Char(related='picture_id.filename', readonly=True)

    def _compute_picture(self):
        Pic = self.env['pdp.picture']
        Product = self.env['pdp.product']
        for w in self:
            products = Product.search([('model_id', '=', w.model_id.id)])
            w.picture_id = Pic.search([('product_ids', 'in', products.ids)], limit=1) if products else Pic.browse()
