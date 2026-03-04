from odoo import models, fields


class SisDocType(models.Model):
    _name = 'sis.doc.type'
    _description = 'SIS Document Type'
    _rec_name = 'name'

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    category = fields.Selection([
        ('S', 'Sales'),
        ('W', 'Workshop/Production'),
    ], string='Category')
