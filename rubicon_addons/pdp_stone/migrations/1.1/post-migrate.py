import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Backfill stale stone weights.

    _compute_weight_id used to require an exact shade match, so every coloured
    stone (with a shade) failed to find its shadeless weight row and was left
    at 0. The compute now matches on type/shape/size only, but the stored
    weight_id values do not refresh on upgrade — recompute them once here.

    Product-stone weights that depend on these are refreshed by pdp_product's
    own migration (pdp.product.stone is not in the registry yet at this point).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    stones = env['pdp.stone'].search([])
    _logger.info("pdp_stone 1.1: recomputing weight_id for %d stones", len(stones))
    stones._recompute_weight_id()
    env.flush_all()

    with_weight = env['pdp.stone'].search_count([('weight', '>', 0)])
    _logger.info("pdp_stone 1.1: %d/%d stones now have a weight", with_weight, len(stones))
