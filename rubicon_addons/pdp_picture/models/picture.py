import hashlib
import base64
from odoo import models, fields, api

class Picture(models.Model):
    _name = 'pdp.picture'
    _description = 'Picture linked to a PDP model'
    
    scope = fields.Selection(
        [('product', 'Product'), ('model', 'Model')],
        string='Scope',
        default='product',
        required=True,
        help="'Product' = specific to the products in the list. "
             "'Model' = shared thumbnail shown for all products of the model.",
    )

    product_ids = fields.Many2many(
        comodel_name='pdp.product',
        relation='pdp_picture_product_rel',
        column1='picture_id',
        column2='product_id',
        string='Products',
        help="Products this picture is linked to. Removing a product here does not delete the picture.",
    )

    # Actual image payload -> stored in filestore thanks to attachment=True
    image_1920 = fields.Image(string='Image', max_width=1920, max_height=1920, required=False)
    image = fields.Image(related='image_1920', readonly=False, string=False)  # tu continues à utiliser "image"

    filename = fields.Char(string='Filename')
    
    checksum = fields.Char(string='Checksum', index=True)
    
    # Drawing (Sketch) support
    drawing_1920 = fields.Image(string='Drawing', max_width=1920, max_height=1920, required=False)
    drawing = fields.Image(related='drawing_1920', readonly=False, string=False)
    drawing_filename = fields.Char(string='Drawing Filename')

    active = fields.Boolean(default=True)

    # Traceability to original Pictures database
    source_date = fields.Datetime(
        string='Source Date',
        readonly=True,
        help="LastUpdated value from the original Pictures SQL Server database.",
    )

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