from odoo import fields, models

class ProductAddonCost(models.Model):
    """
    B002-DTS/W,PNT,US,4.00
    B002-DTS/W,PT2,US,.00
    B002-DTS/W,SLD,US,.00
    """
    _name="pdp.addon.cost"
    _description = "Link table product-addon cost"
    
    product_code = fields.Many2one(
        comodel_name="pdp.product",
        ondelete="restrict",
        required=True
    )
    
    addon_code = fields.Many2one(
        comodel_name="pdp.addon.type",
        ondelete="restrict",
        required=True
    )
    
    cost        = fields.Monetary(
        string='Cost',
        currency_field="currency",
        required=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True
    )
    
