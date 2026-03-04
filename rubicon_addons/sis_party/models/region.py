from odoo import models, fields


class SisRegion(models.Model):
    _name = 'sis.region'
    _description = 'SIS Region'
    _rec_name = 'name'

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
