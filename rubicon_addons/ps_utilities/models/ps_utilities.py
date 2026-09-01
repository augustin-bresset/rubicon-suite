from odoo import api, models


class PsUtilities(models.TransientModel):
    """Backend helpers for the PSUtilities client action.

    Mirrors the legacy PSUtilities app: an "Invoice Select" screen (designs of a
    sales invoice with their PDP white-gold reference) and a "Parts Update" screen
    (bulk reassign the part of pdp.product.part records).
    """
    _name = 'ps.utilities'
    _description = 'PSUtilities helper methods'

    # ── Invoice Select ─────────────────────────────────────────────────────
    @api.model
    def get_invoices(self):
        """Sales invoices (SI) for the Invoice dropdown."""
        docs = self.env['sis.document'].search(
            [('doc_type_code', '=', 'SI')], order='name desc')
        return [{'id': d.id, 'name': d.name} for d in docs]

    @api.model
    def get_invoice_designs(self, doc_id):
        """For an invoice: each line's Design, its PDP-Design (the /W reference
        product code resolved at import) and whether a PDP product matched."""
        doc = self.env['sis.document'].browse(doc_id)
        return [{
            'design': item.design or '',
            'pdp_design': item.product_id.code or '',
            'selected': bool(item.product_id),
        } for item in doc.item_ids.sorted(lambda i: (i.sequence, i.id))]

    # ── Parts Update ───────────────────────────────────────────────────────
    @api.model
    def get_parts(self):
        """All parts for the filter / target dropdowns."""
        parts = self.env['pdp.part'].search([], order='code')
        return [{'id': p.id, 'code': p.code, 'name': p.name} for p in parts]

    @api.model
    def search_product_parts(self, model_code=None, part_id=None, limit=1000):
        """pdp.product.part rows filtered by model code and/or part."""
        domain = []
        if model_code:
            domain.append(('product_id.model_id.code', '=', model_code.strip()))
        if part_id:
            domain.append(('part_id', '=', int(part_id)))
        recs = self.env['pdp.product.part'].search(domain, limit=limit, order='id')
        return [{
            'id': r.id,
            'design': r.product_id.code or '',
            'part_name': r.part_id.name or '',
            'part_code': r.part_id.code or '',
        } for r in recs]

    @api.model
    def update_product_parts(self, line_ids, new_part_id):
        """Reassign the part on the given pdp.product.part rows. Returns the count."""
        if not line_ids or not new_part_id:
            return 0
        recs = self.env['pdp.product.part'].browse(line_ids).exists()
        recs.write({'part_id': int(new_part_id)})
        return len(recs)
