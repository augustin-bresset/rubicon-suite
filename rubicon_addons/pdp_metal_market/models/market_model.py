# rubicon_addons/pdp_metal_market/models/market_models.py
from odoo import models, fields, api

class MarketMetal(models.Model):
    _name = "pdp.market.metal"
    _description = "Base commodity metal"
    _order = "code"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    base_unit = fields.Selection([('troy_oz', 'Troy ounce'), ('gram', 'Gram')], default='troy_oz', required=True)
    base_currency_id = fields.Many2one('res.currency', required=True, default=lambda s: s.env.ref('base.USD'))

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Metal code must be unique.')
    ]


class MarketPrice(models.Model):
    _name = "pdp.market.price"
    _description = "Daily spot price per metal"
    _order = "date desc"

    metal_id = fields.Many2one('pdp.market.metal', required=True, index=True, ondelete='cascade')
    date = fields.Date(required=True, index=True)
    price = fields.Monetary(currency_field='currency_id', required=True)
    currency_id = fields.Many2one(related='metal_id.base_currency_id', store=True, readonly=True)
    source_id = fields.Many2one('pdp.market.source')

    _sql_constraints = [
        ('uniq_metal_date', 'unique(metal_id, date)', 'One price per metal and date.')
    ]


class MarketSource(models.Model):
    _name = "pdp.market.source"
    _description = "Spot price source"

    name = fields.Char(required=True)
    type = fields.Selection([('manual','Manual'), ('csv','CSV'), ('api','API')], default='manual')
    config_json = fields.Text()
