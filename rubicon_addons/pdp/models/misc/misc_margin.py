from odoo import models, fields

class MiscMargin(models.Model):
    _name = 'rubicon.misc.margin'
    _table = 'margin_miscs'
    _description = 'Miscellaneous Margin'

    type  = fields.Char(string='Type', required=True, size=20)
    ratio = fields.Float(
        string='Ratio',
        digits=(6, 4),
        required=True,
    )
