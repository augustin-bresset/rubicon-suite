from odoo import models, fields

class Stone(models.Model):
    """
    
    stone code format : {type_code}{shade_code}-{shape_code}-{size}
    """

    _name = 'pdp.stone'
    _description = 'Stone'

    _rec_name = 'code'

    code        = fields.Char(
        string="Stock Code", 
        required=True,
    )

    type_code   = fields.Many2one(
        comodel_name='pdp.stone.type',
        string='Stone Type',
    )
    shape_code  = fields.Many2one(
        comodel_name='pdp.stone.shape',
        string='Stone Shape',
    )
    shade_code  = fields.Many2one(
        comodel_name='pdp.stone.shade',
        string='Stone Shade',
    )
    size        = fields.Many2one(
        comodel_name='pdp.stone.size',
        string='Stone Size',
    )
    cost        = fields.Monetary(
        string='Cost',
        currency_field="currency",
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
    )
    
    @staticmethod
    def get_stone_code(stone_type, stone_shade, stone_shape, size):
        stone_type = stone_type.replace(' ', '')
        stone_shade = stone_shade.replace(' ', '')
        stone_shade = stone_shade.replace('1', '')
        stone_shape = stone_shape.replace(' ', '')
        stone_shape = stone_shape.replace('1', '')
        return f"{stone_type}{stone_shade}-{stone_shape}-{size}"