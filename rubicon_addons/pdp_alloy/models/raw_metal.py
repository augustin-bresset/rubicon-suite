from odoo import models, fields


class RawMetal(models.Model):
    _name = 'pdp.raw.metal'
    _description = 'Raw Metal'
    _rec_name = 'code'
    _order = 'code'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    density = fields.Float(
        string='Density (g/cm³)',
        digits=(10, 4),
        default=0.0,
        help='Density in grams per cubic centimetre.',
    )
    price = fields.Monetary(
        string='Price /g',
        currency_field='currency_id',
        default=0.0,
    )
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'Raw metal code must be unique.'),
    ]
