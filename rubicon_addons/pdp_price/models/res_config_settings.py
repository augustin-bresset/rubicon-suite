from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pdp_weight_uom_name = fields.Char(
        string="Weight Unit Name",
        default='g',
        config_parameter='pdp.weight.uom.name',
        help="Unit name used for weight display (e.g. 'g', 'oz')."
    )
