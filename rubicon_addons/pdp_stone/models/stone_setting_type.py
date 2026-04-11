from odoo import models, fields


class StoneSettingType(models.Model):
    _name = 'pdp.stone.setting.type'
    _description = 'Stone Setting Type'
    _order = 'cost'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    cost = fields.Monetary(string='Cost', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
