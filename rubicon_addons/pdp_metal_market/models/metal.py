from odoo import fields, models


class Metal(models.Model):
    """Link a PDP metal to the market commodity its spot price comes from.

    Lives here, not in pdp_metal: the base metal model must not reference a
    model of the market module (pdp_metal_market depends on pdp_metal, not the
    other way round).
    """
    _inherit = 'pdp.metal'

    market_metal_id = fields.Many2one(
        'pdp.market.metal',
        string='Market Metal',
        help='Commodity whose daily spot price is used when the cost method is "Market Price".',
    )
