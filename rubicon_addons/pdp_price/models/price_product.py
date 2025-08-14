# models/price_product.py
from odoo import models, fields, api

class PriceProduct(models.Model):
    _name = 'pdp.price.product'
    _description = 'Stored Product Price'

    product_id = fields.Many2one('pdp.product', required=True, ondelete='cascade')
    margin_id  = fields.Many2one('pdp.margin')
    date = fields.Date(required=True, default=fields.Date.context_today)
    currency_id = fields.Many2one('res.currency', required=True,
                                  default=lambda self: self.env.company.currency_id)

    # Totaux
    cost = fields.Monetary(currency_field='currency_id')
    margin = fields.Monetary(currency_field='currency_id')
    price = fields.Monetary(currency_field='currency_id')

    # Détail JSON (option simple) ou One2many dans un autre modèle persistant
    detail_json = fields.Json()

    def action_fill_from_preview(self):
        # ouvre le wizard avec default_…, puis à la fermeture un on_close crée l’enregistrement
        action = self.env.ref('pdp_price.action_pdp_price_preview').read()[0]
        action['context'] = {
            'default_product_id': self.product_id.id,
            'default_margin_id': self.margin_id.id,
            'default_currency_id': self.currency_id.id,
            'default_date': self.date,
        }
        return action
