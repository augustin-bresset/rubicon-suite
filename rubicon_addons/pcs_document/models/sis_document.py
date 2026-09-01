from odoo import api, models
from odoo.exceptions import UserError


class SisDocument(models.Model):
    """SIS-side stock card generation (the legacy 'SIS Report' tool).

    Stock cards can be printed for any sales order, registered in
    production or not: barcodes follow the same generation rules either
    way, so a card printed before the PCS registration still scans
    correctly once the document is added to production.
    """
    _inherit = 'sis.document'

    def _get_stock_card_datas(self):
        """One stock card data dict per document item.

        Uses the real pcs.barcode records when the document is in
        production; otherwise builds transient new() records so the same
        card logic (barcode name, stamp, stones, photo) applies.
        """
        self.ensure_one()
        pcs_doc = self.env['pcs.document'].with_context(
            active_test=False).search(
                [('sis_document_id', '=', self.id)], limit=1)
        if pcs_doc and pcs_doc.barcode_ids:
            return [barcode.get_stock_card_data()
                    for barcode in pcs_doc.barcode_ids.sorted('line_no')]

        transient_doc = self.env['pcs.document'].new(
            {'sis_document_id': self.id})
        cards = []
        items = self.item_ids.sorted(lambda i: (i.sequence, i.id))
        for line_no, item in enumerate(items, start=1):
            barcode = self.env['pcs.barcode'].new({
                'document_id': transient_doc.id,
                'item_id': item.id,
                'line_no': line_no,
            })
            barcode._sync_from_item()
            cards.append(barcode.get_stock_card_data())
        return cards

    def action_print_stock_cards(self):
        if not self.mapped('item_ids'):
            raise UserError("This sales order has no item to print.")
        report = self.env.ref('pcs_document.action_report_stock_card_sis')
        return report.report_action(self)

    # ── System Setting (legacy SIS Report > Setting window) ───────────────

    @api.model
    def get_labor_minute_rates(self):
        Barcode = self.env['pcs.barcode']
        return {
            'filling': Barcode._labor_minute_rate('filing'),
            'setting': Barcode._labor_minute_rate('setting'),
        }

    @api.model
    def set_labor_minute_rates(self, filling, setting):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('pcs.labor_minute_rate_filing', str(float(filling)))
        params.set_param('pcs.labor_minute_rate_setting', str(float(setting)))
        return True

    # ── Selectors of the SIS Report window (Year -> Ref) ───────────────────

    @api.model
    def get_stock_card_years(self):
        self.env.cr.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM date_created)::int AS year
            FROM sis_document
            WHERE doc_type_code = 'SO' AND date_created IS NOT NULL
            ORDER BY year DESC
        """)
        return [row[0] for row in self.env.cr.fetchall()]

    @api.model
    def get_stock_card_orders(self, year):
        year = int(year)
        docs = self.search([
            ('doc_type_code', '=', 'SO'),
            ('date_created', '>=', '%d-01-01' % year),
            ('date_created', '<=', '%d-12-31' % year),
        ], order='name desc')
        return [{'id': d.id, 'name': d.name} for d in docs]
