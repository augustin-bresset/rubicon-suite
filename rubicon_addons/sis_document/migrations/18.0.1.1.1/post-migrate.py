import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Recompute document totals after widening profit_pct to 4 decimals.

    sis.document.profit_pct went from digits (6, 2) to (6, 4) so the document
    rollup matches the line precision (e.g. 0.6521 -> 65.21 %). The column was
    altered in place, so existing rows still hold the 2-decimal value; recompute
    them from the lines. (No-op when there are no documents.)
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    docs = env['sis.document'].search([])
    if not docs:
        _logger.info("sis_document 1.1.1: no documents to recompute.")
        return
    docs._compute_totals()
    docs.flush_recordset(['total_qty', 'total_amount', 'total_cost',
                          'total_profit', 'profit_pct'])
    _logger.info("sis_document 1.1.1: recomputed totals for %d document(s).", len(docs))
