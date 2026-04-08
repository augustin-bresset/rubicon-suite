from odoo import models, fields


class PdpLaborSettings(models.Model):
    _name = 'pdp.labor.settings'
    _description = 'PDP Labor Settings'

    default_labor_currency_id = fields.Many2one(
        'res.currency',
        string='Default Labor Currency',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'THB')], limit=1),
        required=True,
    )
