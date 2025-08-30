from odoo import fields, models

class LaborCostModel(models.Model):
    """
    B009-PLAIN GOLD/W,CAS,TH,.00
    B009-PLAIN GOLD/W,FIL,TH,.00
    B009-PLAIN GOLD/W,LAB,TH,.00
    """
    _name="pdp.labor.cost.model"
    _description="Link table model-addon cost"
    
    model_id = fields.Many2one(
        comodel_name="pdp.product.model",
        ondelete="restrict",
        required=True,
        index=True
    )
    metal = fields.Char(
        string="Metal",
        required=True,
        default="W"
    )
    
    labor_id = fields.Many2one(
        comodel_name="pdp.labor.type",
        ondelete="restrict",
        required=True,
        index=True
    )
    
    cost        = fields.Monetary(
        string='Cost',
        currency_field="currency_id",
        required=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True
    )