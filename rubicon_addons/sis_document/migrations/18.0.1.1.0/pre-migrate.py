import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Surface legacy documents whose stored totals diverge from their items.

    total_amount/total_cost/total_profit/total_qty become computed (sum of the
    lines) in 18.0.1.1.0, so Odoo will recompute them. Before that overwrites
    anything, log any document whose stored total_amount differs from the sum
    of its items, so a historical figure is never changed silently. (No-op when
    there are no documents.)
    """
    cr.execute("""
        SELECT d.name, d.total_amount, COALESCE(SUM(i.amount), 0.0) AS items_amount
        FROM sis_document d
        LEFT JOIN sis_document_item i ON i.document_id = d.id
        GROUP BY d.id, d.name, d.total_amount
        HAVING ABS(COALESCE(d.total_amount, 0.0) - COALESCE(SUM(i.amount), 0.0)) > 0.01
        ORDER BY ABS(COALESCE(d.total_amount, 0.0) - COALESCE(SUM(i.amount), 0.0)) DESC
    """)
    rows = cr.fetchall()
    if not rows:
        _logger.info("sis_document 1.1: stored totals match their items (or no documents).")
        return
    _logger.warning(
        "sis_document 1.1: %d document(s) have a stored total_amount differing from "
        "the sum of their items; it will be recomputed from the lines:", len(rows))
    for name, stored, items_amount in rows[:50]:
        _logger.warning("  %s: stored=%.2f items=%.2f", name, stored or 0.0, items_amount or 0.0)
