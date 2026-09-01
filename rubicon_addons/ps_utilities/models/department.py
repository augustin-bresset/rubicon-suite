from odoo import models, fields


class PcsDepartment(models.Model):
    _name = 'pcs.department'
    _description = 'PCS Department'
    _rec_name = 'name'
    _order = 'code'

    _sql_constraints = [('code_uniq', 'unique(code)', 'The department code must be unique.')]

    code = fields.Char(string='ID', required=True, index=True)
    name = fields.Char(string='Department', required=True)
    group_id = fields.Many2one('pcs.dept.group', string='Group')
    loss_pct = fields.Float(string='Loss %')
    sequence = fields.Integer(string='Seq No', default=10)

    # Flags (mirrors the legacy boolean columns)
    transfer_stones = fields.Boolean(string='T/Stones')
    stones = fields.Boolean(string='Stones')
    transfer_metals = fields.Boolean(string='T/Metals')
    metals = fields.Boolean(string='Metals')
    transfer_parts = fields.Boolean(string='T/Parts')
    parts = fields.Boolean(string='Parts')
    auto_weight = fields.Boolean(string='Auto Wht.')
    p_loss_pct = fields.Boolean(string='P/Loss%')
    clear = fields.Boolean(string='Clear')
