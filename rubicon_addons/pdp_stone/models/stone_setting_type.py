from odoo import models, fields


class StoneSettingType(models.Model):
    _name = 'pdp.stone.setting.type'
    _description = 'Stone Setting Type'
    _order = 'cost'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    cost = fields.Float(string='Cost (THB)', digits=(10, 2), required=True)
