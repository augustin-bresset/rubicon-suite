from odoo import models, fields

class GoldPurity(models.Model):
    _name = 'rubicon.gold.purity'
    _table = 'gold_purities'
    _description = 'Gold Purity'
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'The name must be unique!'),
    ]

    name    = fields.Char(string='Name (e.g. 18K)', required=True, size=3)
    percent = fields.Float(
        string='Percentage',
        digits=(4, 1),
        help='e.g. 75.0 for 18K gold',
    )
