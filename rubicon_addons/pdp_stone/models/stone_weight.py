from odoo import models, fields

class StoneWeight(models.Model):
    """Weight for a specific type, shape, shade and size of stone.
    It is used mainly because you don't have to specify the shape or shade for having result.
    """
    _name = "pdp.stone.weight"
    _description = "Stone Weight"


    weight = fields.Float(
        string='Weight (carat)',
        digits=(7, 4),
        required=True
    )
    type_code = fields.Many2one(        
        comodel_name="pdp.stone.type",
        string="Type",    
    )
    
    shape_code = fields.Many2one(
        comodel_name="pdp.stone.shape",
        string="Shape",
    )

    shade_code = fields.Many2one(
        comodel_name="pdp.stone.shade",
        string="Shade"
    )

    size = fields.Many2one(
        comodel_name="pdp.stone.size",
        string="Size"
    )
