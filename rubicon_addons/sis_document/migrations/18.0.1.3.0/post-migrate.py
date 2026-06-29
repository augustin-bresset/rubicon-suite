import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Backfill sis.document.item.product_id from the design code.

    Until now the FK to pdp.product was never populated; the workspace
    resolved products by matching the design string against product.code.
    Linking the FK lets the UI use the stable product id and lets a later
    code migration rename products without breaking historical documents.
    Idempotent: re-running only touches still-unlinked items.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    result = env['sis.document.item']._backfill_product_links()
    _logger.info(
        "sis_document 1.3: linked %(linked)d item(s) to a PDP product by design; "
        "%(unmatched)d item(s) had no matching product code.", result)
