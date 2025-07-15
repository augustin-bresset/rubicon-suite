from odoo import models, fields

class Region(models.Model):
    _name = 'rubicon.misc.region'
    _table = 'regions'
    _description = 'Region'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    code        = fields.Char(string='Code', required=True, size=2)
    name        = fields.Char(string='Name', required=True, size=40)
    country_ids = fields.One2many(
        comodel_name='rubicon.misc.country',
        inverse_name='region_id',
        string='Countries',
    )
