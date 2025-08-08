from odoo import fields, models

class ModelLaborCost(models.Model):
    """
    B009-PLAIN GOLD/W,CAS,TH,.00
    B009-PLAIN GOLD/W,FIL,TH,.00
    B009-PLAIN GOLD/W,LAB,TH,.00
    """
    _name="pdp.labor.cost.model"
    _description="Link table model-addon cost"
    
    model_code = fields.Many2one(
        comodel_name="pdp.product.model",
        ondelete="restrict",
        required=True
    )
    metal_code = fields.Char(
        string="Metal",
        required=True,
        default="W"
    )
    
    labor_code = fields.Many2one(
        comodel_name="pdp.labor.type",
        ondelete="restrict",
        required=True   
    )
    
    cost        = fields.Monetary(
        string='Cost',
        currency_field="currency",
        required=True
    )
    
    currency    = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True
    )
    
