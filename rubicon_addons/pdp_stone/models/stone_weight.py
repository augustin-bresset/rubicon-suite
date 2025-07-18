from odoo import models, fields

class StoneWeight(models.Model):
    """Weight for a specific type, shape, shade and size of stone.
    It is used mainly because you don't have to specify the shape or shade for having result.
    """
    _name = "pdp.stone.weight"
    _description = "Stone Weight"


    weight = fields.Float(
        string='Weight (carat)',
        digits=(5, 2),
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
