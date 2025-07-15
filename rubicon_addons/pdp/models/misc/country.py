from odoo import models, fields

class Country(models.Model):
    _name = 'rubicon.misc.country'
    _table = 'countries'
    _description = 'Country'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    code      = fields.Char(string='Code', required=True, size=2)
    name      = fields.Char(string='Name', required=True, size=40)
    region_id = fields.Many2one(
        comodel_name='rubicon.misc.region',
        string='Region',
        ondelete='set null',
    )
