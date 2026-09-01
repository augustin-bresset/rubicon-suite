from odoo import models, fields


class PcsEmployee(models.Model):
    _name = 'pcs.employee'
    _description = 'PCS Employee'
    _rec_name = 'name'
    _order = 'code'

    _sql_constraints = [('code_uniq', 'unique(code)', 'The employee code must be unique.')]

    code = fields.Char(string='Id', required=True, index=True)
    name = fields.Char(string='Employee', required=True)
    type_id = fields.Many2one('pcs.employee.type', string='Type')
    tag = fields.Char(string='Tag')
    active = fields.Boolean(string='Active', default=True)
    department_ids = fields.Many2many('pcs.department', string='Departments')
