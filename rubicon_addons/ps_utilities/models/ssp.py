from odoo import models, fields


class PcsSsp(models.Model):
    _name = 'pcs.ssp'
    _description = 'PCS Solder/Spring/Plate'
    _rec_name = 'name'
    _order = 'code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The SSP code must be unique.'),
    ]

    code = fields.Char(string='ID', required=True)
    name = fields.Char(string='SSP', required=True)
