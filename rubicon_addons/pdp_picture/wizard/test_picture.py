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
        for w in self:
            w.picture_id = Pic.search([('model_id', '=', w.model_id.id)], limit=1)
