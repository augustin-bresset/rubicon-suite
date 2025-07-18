from odoo import models, fields

class StoneLot(models.Model):
    _name = "pdp.stone.weight"
    _description = "Stone Weight"

    code  = fields.Char(string="Code", readonly=False)
    cost = fields.Monetary(
        string='Cost',
        digits=(10, 2),
        currency_field='currency_id',
        required=True,
    )
    
    type_code = fields.Many2one(        
        comodel_name="pdp.stone.type",
        string="Type",
        readonly=False,
    )
    
    shape_code = fields.Many2one(
        comodel_name="pdp.stone.shape",
        string="Shape",
        readonly=False,
    )

    shade_code = fields.Many2one(
        comodel_name="pdp.stone.shade",
        string="Shade",
        readonly=False,
    )

    size = fields.Many2one(
        comodel_name="pdp.stone.size",
        string="Size",
        readonly=False,
    )

