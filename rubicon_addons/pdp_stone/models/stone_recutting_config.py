from odoo import models, fields, api


class StoneRecuttigConfig(models.Model):
    _name = 'pdp.stone.recutting.config'
    _description = 'Global Recutting Configuration'

    cost = fields.Monetary(
        string='Recutting Cost /ct',
        currency_field='currency_id',
        default=50.0,
    )
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)

    @api.model
    def get_config(self):
        """Return the singleton config, creating it with defaults if absent."""
        config = self.search([], limit=1)
        if not config:
            thb = self.env['res.currency'].search([('name', '=', 'THB')], limit=1)
            config = self.create({
                'cost': 50.0,
                'currency_id': thb.id if thb else self.env.company.currency_id.id,
            })
        return config
