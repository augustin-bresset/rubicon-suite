from odoo import models, fields


class SisPayTerm(models.Model):
    _name = 'sis.pay.term'
    _description = 'SIS Payment Term'
    _rec_name = 'name'

    name = fields.Char(required=True)
