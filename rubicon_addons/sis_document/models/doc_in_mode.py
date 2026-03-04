from odoo import models, fields


class SisDocInMode(models.Model):
    _name = 'sis.doc.in.mode'
    _description = 'SIS Document Receiving Mode'
    _rec_name = 'name'

    name = fields.Char(required=True)
