from odoo import models, fields

class MetalParameter(models.Model):
    _name = 'pdp.metal.parameter'
    _description = 'Metal Processing Parameters'
    
    metal_id = fields.Many2one('pdp.metal', string='Metal', required=True)
    name = fields.Char(string='Process Name', required=True, help="E.g. Casting, Handmade, etc.")
    
    loss_percentage = fields.Float(string='Material Loss (%)', help="Percentage of metal lost during process")
    risk_factor = fields.Float(string='Risk Factor', default=1.0, help="Multiplier for risk (e.g. 1.05 for 5% risk)")
    density_difference = fields.Float(string='Density Diff. (%)', help="Percentage of difference between alloy density and reference density")

    composition = fields.Text(string='Composition Details', help="Description of the alloy composition")
