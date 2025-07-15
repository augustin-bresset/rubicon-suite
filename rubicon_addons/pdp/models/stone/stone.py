from odoo import models, fields

class Stone(models.Model):
    _name = 'rubicon.stone'
    _table = 'stones'
    _description = 'Stone'

    stone_type_id = fields.Many2one(
        comodel_name='rubicon.stone.type',
        string='Stone Type',
        required=True,
    )
    shape_id = fields.Many2one(
        comodel_name='rubicon.stone.shape',
        string='Stone Shape',
        required=True,
    )
    shade_id = fields.Many2one(
        comodel_name='rubicon.stone.shade',
        string='Stone Shade',
        required=True,
    )
    size_id = fields.Many2one(
        comodel_name='rubicon.stone.size',
        string='Stone Size',
        required=True,
    )
    weight = fields.Float(
        string='Weight (carat)',
        digits=(5, 2),
    )
    cost = fields.Monetary(
        string='Cost',
        digits=(10, 2),
        currency_field='currency_id',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='rubicon.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env['rubicon.currency'].search([('code', '=', 'USD')], limit=1).id,
    )
    item_id = fields.Many2one(
        comodel_name='rubicon.item',
        string='Related Item',
    )
    lot_ids = fields.One2many(
        comodel_name='rubicon.stone.lot.cost',
        inverse_name='stone_id',
        string='Stone Lots',
    )
