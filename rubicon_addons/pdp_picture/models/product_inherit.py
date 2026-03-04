from odoo import models, fields

class Product(models.Model):
    _name = 'pdp.product'
    _inherit = ['pdp.product', 'image.mixin']
