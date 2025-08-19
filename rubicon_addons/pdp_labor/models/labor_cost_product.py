from odoo import fields, models

class LaborCostProduct(models.Model):
    """
    B009-PLAIN GOLD/W,CAS,TH,.00
    B009-PLAIN GOLD/W,FIL,TH,.00
    B009-PLAIN GOLD/W,LAB,TH,.00
    """
    _name="pdp.labor.cost.product"
    _description="Link table product-addon cost"
    
    product_id = fields.Many2one(
        comodel_name="pdp.product",
        ondelete="restrict",
        required=True,
        index=True
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
        required=True,
        index=True
    )
    
