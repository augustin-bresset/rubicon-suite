# rubicon_addons/pdp_metal_market/models/alloy.py
from odoo import models, fields, api

class MetalAlloy(models.Model):
    _name = "pdp.metal.alloy"
    _description = "Alloy recipe for a market variant"

    name = fields.Char(required=True)
    variant_code = fields.Char(required=True, index=True)
    yield_factor = fields.Float(default=1.0)
    line_ids = fields.One2many('pdp.metal.alloy.line', 'alloy_id', copy=True)

    _sql_constraints = [
        ('variant_unique', 'unique(variant_code)', 'Variant code must be unique.'),
    ]


class MetalAlloyLine(models.Model):
    _name = "pdp.metal.alloy.line"
    _description = "Alloy components"
    _order = "id"

    alloy_id = fields.Many2one('pdp.metal.alloy', required=True, ondelete='cascade')
    metal_id = fields.Many2one('pdp.market.metal', required=True)
    ratio = fields.Float(required=True, help='Fraction in [0,1]; sum of lines should be 1.0')
