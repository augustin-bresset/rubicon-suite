from odoo import models, fields

class Margin(models.Model):
    _name = 'rubicon.margin'
    _table = 'margins'
    _description = 'Margin'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    code      = fields.Char(string='Code', required=True, size=10)
    name      = fields.Char(string='Name', required=True, size=40)
    percent   = fields.Float(
        string='Percentage',
        digits=(5, 2),
        required=True,
    )
    is_active = fields.Boolean(string='Active', default=True)
