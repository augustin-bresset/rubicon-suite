from odoo import fields, models

class MarginAddon(models.Model):
    """
    Labor addon. 
    """
    _name="pdp.margin.addon"
    
    margin = fields.Float(
        string="Margin",
        digits=(5, 3),
        required=True,
    )

    addon_code = fields.Many2one(
        string="Addon Code",
        comodel_name="pdp.addon.type"
    )
    margin_code = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin")

