from odoo import models, fields, api


class PdpConfig(models.Model):
    _name = 'pdp.config'
    _description = 'PDP Configuration'

    name = fields.Char(default='PDP Configuration', readonly=True)

    labor_currency_id = fields.Many2one(
        'res.currency',
        string='Default Labor / Misc Currency',
        required=True,
        help='Currency applied by default to all labor and misc costs entered in the workspace.',
    )

    @api.model
    def get_singleton(self):
        """Return the unique config record (create with THB default if missing)."""
        config = self.search([], limit=1)
        if not config:
            thb = self.env['res.currency'].search([('name', '=', 'THB')], limit=1)
            config = self.create({'labor_currency_id': thb.id if thb else False})
        return config
