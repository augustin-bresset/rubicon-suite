from odoo import models, fields


class PcsUser(models.Model):
    _name = 'pcs.user'
    _description = 'PCS User'
    _rec_name = 'name'
    _order = 'code'

    _sql_constraints = [('code_uniq', 'unique(code)', 'The user code must be unique.')]

    code = fields.Char(string='ID', required=True, index=True)
    name = fields.Char(string='Name', required=True)
    role_id = fields.Many2one('pcs.role', string='Role')
    active = fields.Boolean(string='Active', default=True)
