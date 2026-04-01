from odoo import models, fields, api

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
    shade_id = fields.Many2one("pdp.stone.shade", string="Stone Shade", index=True)
    size_id  = fields.Many2one("pdp.stone.size",  string="Stone Size",  required=True, index=True, ondelete="restrict")
    weight_id = fields.Many2one(
        'pdp.stone.weight',
        string="Stone Weight Reference",
        compute='_compute_weight_id',
        store=True,
        
    )
    weight = fields.Float(
        string='Weight (carat)',
        related='weight_id.weight',
        readonly=True,
        digits=(7, 4),
        store=True,
    )

    
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
        ("stone_tuple_uniq", "unique(type_id, shape_id, shade_id, size_id)", "This stone combination already exists."),
        ("cost_currency_chk", "CHECK (cost IS NULL OR currency_id IS NOT NULL)", "Currency required when a cost is set."),
    ]
    
    @api.depends('type_id', 'shape_id', 'size_id', 'shade_id')
    def _compute_weight_id(self):
        for record in self:
            if record.type_id and record.shape_id and record.size_id:
                domain = [
                    ('type_id', '=', record.type_id.id),
                    ('shape_id', '=', record.shape_id.id),
                    ('size_id', '=', record.size_id.id),
                    ('shade_id', '=', record.shade_id.id if record.shade_id else False),
                ]
                weight_record = self.env['pdp.stone.weight'].search(domain, limit=1)
                record.weight_id = weight_record.id if weight_record else False
            else:
                record.weight_id = False
                
    @staticmethod
    def get_stone_code(type, shade, shape, size):
        type = type.replace(' ', '')
        shade = shade.replace(' ', '')
        shade = shade.replace('1', '')
        shape = shape.replace(' ', '')
        shape = shape.replace('1', '')
        return f"{type}{shade}-{shape}-{size}"