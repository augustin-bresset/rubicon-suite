from odoo import models, fields


class RubiconUom(models.Model):
    _name = 'rubicon.uom'
    _description = 'Unit of Measure'
    _rec_name = 'symbol'

    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(string='Symbol', required=True)
    category_id = fields.Many2one('rubicon.uom.category', string='Category', required=True, ondelete='cascade')
    is_reference = fields.Boolean(string='Is Reference Unit', default=False)
    is_global_default = fields.Boolean(string='Is Global Default', default=False)
