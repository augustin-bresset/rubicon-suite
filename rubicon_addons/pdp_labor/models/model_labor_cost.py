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
    
    # labor_cost      = fields.Float(string="Labor Cost", digits=(10, 3))
    # casting_cost    = fields.Float(string="Casting Cost", digits=(10, 3)) 
    # filing_cost     = fields.Float(string="Filing Cost", digits=(10, 3))
    # polishing_cost  = fields.Float(string="Polishing Cost", digits=(10, 3))
    
    labor_code = fields.Many2one(
        comodel_name="pdp.labor.type",
        ondelete="restrict",
        required=True   
    )
    
    cost = fields.Float(
        string="Cost (TBH)",
        digits=(10, 2)
    )
    
