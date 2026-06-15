from odoo import models, fields


class PdpCurrencySetting(models.Model):
    _name = 'pdp.currency.setting'
    _description = 'Currency rates offered in PDP workspace'
    _rec_name = 'currency_id'
    _order = 'sequence, id'

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        ondelete='cascade',
    )
    rate = fields.Float(
        string='Rate',
        digits=(12, 6),
        default=1.0,
        help='Custom rate to apply in PDP pricing (e.g. 1.0 for USD, 0.92 for EUR).',
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_currency', 'UNIQUE(currency_id)', 'Each currency can only appear once.'),
    ]
