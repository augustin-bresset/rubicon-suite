from odoo import models, fields


class PcsDeptGroup(models.Model):
    _name = 'pcs.dept.group'
    _description = 'PCS Department Group'
    _rec_name = 'name'
    _order = 'code'

    _sql_constraints = [('code_uniq', 'unique(code)', 'The group code must be unique.')]

    code = fields.Char(string='ID', required=True, index=True)
    name = fields.Char(string='Dept. Group', required=True)
    type = fields.Char(string='Type')
    sequence = fields.Integer(string='Seq', default=10)
