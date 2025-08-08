from odoo import models, fields, api

class PriceComponent(models.TransientModel):
    _name = 'pdp.price.component'
    _description = 'Abstract Base Component'

    
    def compute(self, product_code, margin_code, currency, date):
        """Return dict(type, cost, margin, price). Must be overridden."""
        raise NotImplementedError        
    
    @api.model
    def _convert(self, amount, from_cur, to_cur, date=None):
        return from_cur._convert(
            from_amount=amount, 
            to_currency=to_cur, 
            company=self.env.company, 
            date=date or fields.Date.context_today(self)
            )

    @api.model
    def compute_payload(self, type_, cost, margin, currency):
        cost = currency.round(cost or 0.0)
        margin = currency.round(margin or 0.0)
        return {'type': type_, 'cost': cost, 'margin': margin, 'price': cost + margin}
