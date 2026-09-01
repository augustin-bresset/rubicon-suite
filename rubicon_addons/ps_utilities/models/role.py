from odoo import models, fields


class PcsRole(models.Model):
    _name = 'pcs.role'
    _description = 'PCS Role'
    _rec_name = 'name'
    _order = 'code'

    _sql_constraints = [('code_uniq', 'unique(code)', 'The role code must be unique.')]

    code = fields.Char(string='ID', required=True, index=True)
    name = fields.Char(string='Role', required=True)
