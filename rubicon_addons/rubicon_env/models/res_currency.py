from odoo import api, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _rubicon_ensure_active(self, names):
        """Activate the currencies the suite relies on (THB company currency,
        USD and EUR of the PDP currency settings).

        Called from data/res_currency.xml on every install or update: a
        ``<record id="base.THB">`` would only apply at first install, because
        base ships its currencies as noupdate data, and the reference CSVs
        (``pdp.stone.csv`` etc.) fail to load when THB is inactive.
        """
        currencies = self.with_context(active_test=False).search([('name', 'in', names)])
        currencies.filtered(lambda c: not c.active).write({'active': True})
        return True
