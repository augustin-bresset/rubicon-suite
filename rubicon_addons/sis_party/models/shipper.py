from odoo import models, fields


class SisShipper(models.Model):
    _name = 'sis.shipper'
    _description = 'SIS Shipper'
    _rec_name = 'name'

    name = fields.Char(required=True)
