from odoo import models, fields

class PdpPrice(models.Model):
    _name = 'pdp.price'

    margin_code = fields.One2many('pdp.margin')
    design = fields.Char()
    purity = fields.Char()
    price_lines = fields.One2many('pdp.price.line', 'price_id')
