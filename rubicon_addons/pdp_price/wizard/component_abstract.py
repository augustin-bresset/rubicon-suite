# wizard/component_abstract.py
from odoo import models, fields, api

class PriceComponent(models.TransientModel):
    _name = 'pdp.price.component'
    _description = 'Abstract Base Component'

    @api.model
    def compute(self, *, product, margin, currency, date):
        """Return dict(type, cost, margin, price). Must be overridden."""
        raise NotImplementedError

    @api.model
    def _convert(self, amount, from_cur, to_cur, date):
        return from_cur._convert(amount, to_cur, self.env.company, date)

    @api.model
    def _payload(self, type_, cost, margin, currency):
        cost = currency.round(cost or 0.0)
        margin = currency.round(margin or 0.0)
        return {'type': type_, 'cost': cost, 'margin': margin, 'price': cost + margin}

    # @api.model
    # def compute_payload(self, *args, **kwargs):
    #     return self._payload(*args, **kwargs)
    
    