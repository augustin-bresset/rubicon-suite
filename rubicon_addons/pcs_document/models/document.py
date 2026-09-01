from odoo import models, fields, api
from odoo.exceptions import UserError


class PcsDocument(models.Model):
    """A sales order registered in production.

    Created from an existing sis.document by its reference (the legacy 'Add
    Document' flow): one piece barcode is generated per document item.
    """
    _name = 'pcs.document'
    _description = 'PCS Production Document'
    _rec_name = 'name'
    _order = 'name desc'

    _sql_constraints = [
        ('sis_document_uniq', 'unique(sis_document_id)',
         'This sales document is already in production.'),
    ]

    sis_document_id = fields.Many2one(
        'sis.document', string='Sales Document', required=True,
        ondelete='restrict', index=True)
    name = fields.Char(
        related='sis_document_id.name', store=True, index=True,
        string='Document')
    date = fields.Date(
        related='sis_document_id.date_created', store=True, string='Date')
    delivery_date = fields.Date(
        related='sis_document_id.date_due', store=True, string='Delv Date')
    active = fields.Boolean(default=True)
    simulated = fields.Boolean(
        default=False,
        help="Set by the factory simulator on the documents it drives, so "
             "the PCS screens can include or exclude simulation data.")
    priority_no = fields.Integer(string='Priority No', default=0)
    barcode_ids = fields.One2many(
        'pcs.barcode', 'document_id', string='Barcodes')
    total_qty = fields.Float(
        compute='_compute_total_qty', string='Total Qty')

    @api.depends('barcode_ids.qty')
    def _compute_total_qty(self):
        for doc in self:
            doc.total_qty = sum(doc.barcode_ids.mapped('qty'))

    # ── Barcode reference ──────────────────────────────────────────────────

    def short_ref(self):
        """'SO-EMA-25114' -> 'EMA25114': the doc-type prefix is dropped and
        the remaining segments are joined, per the legacy barcode format."""
        self.ensure_one()
        parts = (self.name or '').split('-')
        if len(parts) >= 3:
            return ''.join(parts[1:])
        return (self.name or '').replace('-', '')

    # ── Creation from a sales order reference ──────────────────────────────

    @api.model
    def create_from_reference(self, reference):
        """Register a sales document in production and generate its barcodes."""
        reference = (reference or '').strip()
        if not reference:
            raise UserError("Please provide a sales document reference.")
        sis_doc = self.env['sis.document'].search(
            [('name', '=', reference)], limit=1)
        if not sis_doc:
            raise UserError("No sales document found for '%s'." % reference)
        existing = self.with_context(active_test=False).search(
            [('sis_document_id', '=', sis_doc.id)], limit=1)
        if existing:
            raise UserError("Document '%s' is already in production." % reference)
        doc = self.create({'sis_document_id': sis_doc.id})
        doc._sync_barcodes()
        return doc.id

    def _sync_barcodes(self):
        """Create one barcode per document item that has none yet, and refresh
        the PDP/SIS snapshot of existing ones (legacy 'Update PDP')."""
        Barcode = self.env['pcs.barcode']
        for doc in self:
            items = doc.sis_document_id.item_ids.sorted(
                lambda i: (i.sequence, i.id))
            known_items = doc.barcode_ids.mapped('item_id')
            next_no = max(doc.barcode_ids.mapped('line_no') or [0]) + 1
            for item in items:
                if item in known_items:
                    continue
                Barcode.create({
                    'document_id': doc.id,
                    'item_id': item.id,
                    'line_no': next_no,
                })
                next_no += 1
            for barcode in doc.barcode_ids:
                barcode._sync_from_item()

    def action_update_pdp(self):
        self._sync_barcodes()
        return True

    # ── Stock cards ────────────────────────────────────────────────────────

    @api.model
    def action_print_priority_list(self):
        """Print the legacy Priority List: every active document in
        production, ordered by reference."""
        docs = self.search([], order='name')
        if not docs:
            raise UserError("There is no document in production.")
        report = self.env.ref('pcs_document.action_report_priority_list')
        return report.report_action(docs)

    def action_print_stock_cards(self):
        """Print the stock cards of every barcode of the selected documents."""
        barcodes = self.barcode_ids
        if not barcodes:
            raise UserError("There is no barcode to print.")
        report = self.env.ref('pcs_document.action_report_stock_card')
        return report.report_action(barcodes)
