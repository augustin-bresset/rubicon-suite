from odoo import models, fields


class AlloyPurity(models.Model):
    _name = 'pdp.alloy.purity'
    _description = 'Alloy Purity'
    _rec_name = 'code'
    _order = 'percent desc'

    code = fields.Char(string='Code', required=True)
    percent = fields.Float(string='Percent (%)', digits=(10, 2))
    purity_system = fields.Selection([
        ('carat', 'Carat'),
        ('millesimal', 'Millesimal'),
    ], string='System', required=True)

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'Purity code must be unique.'),
    ]
