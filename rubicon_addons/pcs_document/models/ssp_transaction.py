from odoo import models, fields


class PcsSspTransaction(models.Model):
    """Issue/receive of solder, springs and plating material to a worker."""
    _name = 'pcs.ssp.transaction'
    _description = 'PCS Solder/Spring/Plate Transaction'
    _order = 'id desc'

    ssp_id = fields.Many2one('pcs.ssp', string='SSP', required=True)
    department_id = fields.Many2one('pcs.department', string='Dept')
    employee_id = fields.Many2one('pcs.employee', string='Employee')
    purity = fields.Char(string='Purity')
    issue_weight = fields.Float(string='Issue', digits=(10, 3))
    receive_weight = fields.Float(string='Receive', digits=(10, 3))
    date = fields.Date(string='Date', default=fields.Date.context_today)
    user_id = fields.Many2one(
        'res.users', string='By', default=lambda self: self.env.user)
