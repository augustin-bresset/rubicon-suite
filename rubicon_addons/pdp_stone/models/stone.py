from odoo import models, fields

class Stone(models.Model):
    """
    
    stone code format : {type}{shade}-{shape}-{size}
    """

    _name = 'pdp.stone'
    _description = 'Stone'

    _rec_name = 'code'

    code        = fields.Char(
        string="Stock Code", 
        required=True,
        index=True
    )

    type_id  = fields.Many2one("pdp.stone.type",  string="Stone Type",  required=True, index=True)
    shape_id = fields.Many2one("pdp.stone.shape", string="Stone Shape", required=True, index=True)
    shade_id = fields.Many2one("pdp.stone.shade", string="Stone Shade", required=True, index=True)
    size_id  = fields.Many2one("pdp.stone.size",  string="Stone Size",  required=True, index=True)

    
    cost        = fields.Monetary(
        string='Cost',
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
    )
    
    _sql_constraints = [
        ("stone_code_uniq", "unique(code)", "Stone code must be unique."),
        ("stone_tuple_uniq", "unique(type_id, shade_id, shape_id, size_id)", "This stone combination already exists."),
        ("cost_currency_chk", "CHECK (cost IS NULL OR currency_id IS NOT NULL)", "Currency required when a cost is set."),
    ]
    
    @staticmethod
    def get_stone_code(type, shade, shape, size):
        type = type.replace(' ', '')
        shade = shade.replace(' ', '')
        shade = shade.replace('1', '')
        shape = shape.replace(' ', '')
        shape = shape.replace('1', '')
        return f"{type}{shade}-{shape}-{size}"