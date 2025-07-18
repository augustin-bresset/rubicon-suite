from odoo import models, fields

class StoneItem(models.Model):
    _name = 'pdp.stone.item'
    _description = 'Stone'
    _rec_name = 'stock_item_id'


    stock_item_id = fields.Char(
        string="Stock ItemID", 
        readonly=False
    )

    type_code = fields.Many2one(
        comodel_name='pdp.stone.type',
        string='Stone Type',
        required=True,
    )
    shape_code = fields.Many2one(
        comodel_name='pdp.stone.shape',
        string='Stone Shape',
        required=True,
    )
    shade_code = fields.Many2one(
        comodel_name='pdp.stone.shade',
        string='Stone Shade',
        required=True,
    )
    size = fields.Many2one(
        comodel_name='pdp.stone.size',
        string='Stone Size',
        required=True,
    )
    cost = fields.Float(
        string='Cost USD',
        digits=(10, 2),
    )
    
