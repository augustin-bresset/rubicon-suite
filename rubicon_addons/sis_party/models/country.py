from odoo import models, fields


class SisCountry(models.Model):
    _name = 'sis.country'
    _description = 'SIS Country'
    _rec_name = 'name'

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    region_id = fields.Many2one('sis.region', string='Region')
