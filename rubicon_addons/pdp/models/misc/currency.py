from odoo import models, fields

class Currency(models.Model):
    _name = 'rubicon.misc.currency'
    _table = 'currencies'
    _description = 'Currency'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    code   = fields.Char(string='Code', required=True, size=3)
    name   = fields.Char(string='Name', required=True, size=50)
    symbol = fields.Char(string='Symbol', size=5)
