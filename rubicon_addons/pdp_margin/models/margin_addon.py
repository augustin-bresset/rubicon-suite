from odoo import fields, models

class MarginAddon(models.Model):
    """
    Addon Margin 
    """
    _name="pdp.margin.addon"
    _description="Addon Margin"
    
    addon_id = fields.Many2one(
        string="Addon Code",
        comodel_name="pdp.addon.type",
        required=True,
        index=True
    )
    
    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True
        )

    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )