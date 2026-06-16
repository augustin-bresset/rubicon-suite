import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Refresh product-stone original weights.

    pdp.product.stone.weight is a stored computed field reading the catalogue
    weight through stone_id.weight. pdp_stone 1.1 fixed the stone weights, but
    the product-stone stored values stay stale, so recompute them once here
    (this runs after pdp_stone's migration since pdp_product depends on it).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    product_stones = env['pdp.product.stone'].search([])
    _logger.info("pdp_product 1.1: refreshing %d product-stone weights", len(product_stones))
    product_stones.invalidate_recordset(['weight'])
    product_stones._compute_weight()
    env.flush_all()
