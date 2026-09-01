from odoo import models, fields


class PcsEmployeeType(models.Model):
    _name = 'pcs.employee.type'
    _description = 'PCS Employee Type'
    _rec_name = 'name'
    _order = 'code'

    _sql_constraints = [('code_uniq', 'unique(code)', 'The type code must be unique.')]

    code = fields.Char(string='ID', required=True, index=True)
    name = fields.Char(string='Type', required=True)
