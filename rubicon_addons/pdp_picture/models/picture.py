import hashlib
import base64
from odoo import models, fields, api

class Picture(models.Model):
    _name = 'pdp.picture'
    _description = 'Picture linked to a PDP model'
    
    model_id = fields.Many2one(
        'pdp.product.model',
        string='Model',
        ondelete='set null',
        index=True,
        required=False
    )

    # Actual image payload -> stored in filestore thanks to attachment=True
    image_1920 = fields.Image(string='Image', max_width=1920, max_height=1920, required=True)
    image = fields.Image(related='image_1920', readonly=False, string=False)  # tu continues à utiliser "image"

    filename = fields.Char(string='Filename')
    
    checksum = fields.Char(string='Checksum', index=True)
    
    # Drawing (Sketch) support
    drawing_1920 = fields.Image(string='Drawing', max_width=1920, max_height=1920, required=False)
    drawing = fields.Image(related='drawing_1920', readonly=False, string=False)
    drawing_filename = fields.Char(string='Drawing Filename')

    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            payload = vals.get('image') or vals.get('image_1920')
            if payload and not vals.get('checksum'):
                vals['checksum'] = hashlib.md5(base64.b64decode(payload)).hexdigest()
        return super().create(vals_list)

    def write(self, vals):
        payload = vals.get('image') or vals.get('image_1920')
        if payload:
            vals['checksum'] = hashlib.md5(base64.b64decode(payload)).hexdigest()
        return super().write(vals)