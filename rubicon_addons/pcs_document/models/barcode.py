import re
from urllib.parse import quote

from odoo import models, fields, api

# Legacy PBarcode prefix, e.g. 'P01-' or 'S12-', tolerated on scan input.
PBARCODE_PREFIX = re.compile(r'^[PS]\d{2}-')

# Characters encodable in plain Code 39 (the legacy card symbology).
# Anything else (e.g. '&' in old client codes) falls back to Code 128,
# because reportlab silently DROPS invalid characters from a Code 39.
CODE39_SAFE = re.compile(r'^[0-9A-Z\-\. \$/\+%]+$')

# Stamp cell background per metal colour letter (from the legacy stock card:
# yellow gold on yellow, pink gold on salmon).
METAL_STAMP_COLORS = {
    'Y': '#f2df3a',
    'P': '#f08080',
    'R': '#f08080',
    'W': '#e8e8e8',
    'G': '#a8d8a8',
}


class PcsBarcode(models.Model):
    """One physical production piece: a document item under its barcode.

    The barcode follows the legacy format '{CLIENT}{YYNNN}/{N}.{MODEL}',
    e.g. 'EMA25114/5.R2103' for line 5 of SO-EMA-25114, model R2103.
    """
    _name = 'pcs.barcode'
    _description = 'PCS Piece Barcode'
    _rec_name = 'name'
    _order = 'document_id desc, line_no'

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This barcode already exists.'),
    ]

    name = fields.Char(
        string='Barcode', compute='_compute_name', store=True, index=True)
    document_id = fields.Many2one(
        'pcs.document', string='Document', required=True,
        ondelete='cascade', index=True)
    item_id = fields.Many2one(
        'sis.document.item', string='Document Item', ondelete='set null')
    line_no = fields.Integer(string='Line No', required=True, default=1)
    product_id = fields.Many2one('pdp.product', string='PDP Product')
    model_code = fields.Char(string='Model')
    design = fields.Char(string='Design')
    purity = fields.Char(string='Purity')
    metal_code = fields.Char(string='Metal')
    qty = fields.Float(string='Qty', default=1.0)
    size = fields.Char(string='Size')
    tag = fields.Char(string='Tag')
    priority = fields.Boolean(string='Priority', default=False)
    transaction_ids = fields.One2many(
        'pcs.transaction', 'barcode_id', string='Transactions')

    @api.depends('document_id.name', 'line_no', 'model_code')
    def _compute_name(self):
        for barcode in self:
            if not (barcode.document_id and barcode.line_no):
                barcode.name = False
                continue
            barcode.name = '%s/%d.%s' % (
                barcode.document_id.short_ref(),
                barcode.line_no,
                barcode.model_code or '',
            )

    @api.model_create_multi
    def create(self, vals_list):
        barcodes = super().create(vals_list)
        for barcode in barcodes:
            if barcode.item_id:
                barcode._sync_from_item()
        return barcodes

    def _sync_from_item(self):
        """Refresh the SIS/PDP snapshot from the linked document item.

        Uses update() so it also works on transient new() records (the
        SIS-side stock card preview builds cards without storing them).
        """
        for barcode in self:
            item = barcode.item_id
            if not item:
                continue
            product = item.product_id
            barcode.update({
                'product_id': product.id if product else False,
                # The design prefix beats item.model_code as fallback: legacy
                # items sometimes carry a truncated model ('E' for 'E154-...').
                'model_code': (product.model_id.code if product and product.model_id
                               else (item.design or '').split('-')[0]
                               or item.model_code),
                'design': item.design,
                'purity': item.purity,
                'metal_code': item.metal_code,
                'qty': item.qty,
                'size': item.size_remarks,
            })

    @api.model
    def clean_scanned_value(self, value):
        """Normalize scanner input: strip whitespace and a leading legacy
        PBarcode prefix ('P01-EMA25114/5.R2103' -> 'EMA25114/5.R2103')."""
        value = (value or '').strip()
        return PBARCODE_PREFIX.sub('', value)

    # ── Current position in the two production tracks ─────────────────────

    def _last_transaction(self, track=None):
        self.ensure_one()
        txns = self.transaction_ids.sorted(lambda t: t.id)
        if track:
            txns = txns.filtered(lambda t: t.department_id.track == track)
        return txns[-1] if txns else self.env['pcs.transaction']

    def track_status(self, track):
        """(department, 'WIP'|'FIN'|'') of this piece on the given track."""
        txn = self._last_transaction(track)
        if not txn:
            return self.env['pcs.department'], ''
        return txn.department_id, 'WIP' if txn.status == 'wip' else 'FIN'

    # ── Stock card ─────────────────────────────────────────────────────────

    def barcode_image_url(self):
        """Barcode image endpoint: Code 39 without check character (the
        legacy symbology), Code 128 for values Code 39 cannot encode."""
        self.ensure_one()
        if CODE39_SAFE.match(self.name or ''):
            return ('/pcs_document/barcode39?value=%s&width=600&height=90'
                    % quote(self.name or '', safe=''))
        return ('/report/barcode/?barcode_type=Code128&value=%s'
                '&width=600&height=90&humanreadable=0'
                % quote(self.name or '', safe=''))

    def action_print_stock_cards(self):
        report = self.env.ref('pcs_document.action_report_stock_card')
        return report.report_action(self)

    # Cost-to-minutes rates of the legacy stock card, per labor type.
    # Derived from reference cards: filing 180 THB prints 'Filing Min.
    # 128.57' (180/1.4) and a 200 THB setting total prints 137.93
    # (200/1.45). Overridable via ir.config_parameter.
    LABOR_MINUTE_RATES = {'filing': 1.4, 'setting': 1.45}

    def _labor_minute_rate(self, kind):
        default = self.LABOR_MINUTE_RATES[kind]
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'pcs.labor_minute_rate_%s' % kind, str(default))
        try:
            rate = float(raw)
        except ValueError:
            rate = default
        return rate or default

    def _model_labor_cost(self, labor_code):
        """Model-level labor cost for this piece's metal version.

        The imported data holds duplicated rows per (model, labor): the
        most recent one (highest id) is the current version — verified on
        R2103, whose legacy card used 200 THB out of [210, 200].
        """
        self.ensure_one()
        product = self.product_id
        if not (product and product.model_id):
            return 0.0
        lines = self.env['pdp.labor.cost.model'].search([
            ('model_id', '=', product.model_id.id),
            ('labor_id.code', '=', labor_code),
        ], order='id')
        if not lines:
            return 0.0
        exact = lines.filtered(lambda l: l.metal == (self.metal_code or ''))
        return (exact or lines)[-1].cost

    def _gold_weight(self):
        """Model metal weight matching this piece's metal version, with
        purity then first-line fallbacks."""
        self.ensure_one()
        product = self.product_id
        if not (product and product.model_id):
            return 0.0
        lines = product.model_id.metal_weights_ids
        if not lines:
            return 0.0
        exact = lines.filtered(lambda l: l.metal_version == (self.metal_code or ''))
        if not exact:
            exact = lines.filtered(lambda l: l.purity_id.code == (self.purity or ''))
        return (exact[:1] or lines[:1]).weight

    def _metal_letter(self):
        """Colour letter of the metal version ('P3' -> 'P')."""
        match = re.match(r'^([A-Z]+)', self.metal_code or '')
        return match.group(1)[:1] if match else ''

    def get_stock_card_data(self):
        """All the data of one legacy stock card, ready for the QWeb report."""
        self.ensure_one()
        doc = self.document_id
        sis = doc.sis_document_id
        item = self.item_id
        product = self.product_id
        filing_rate = self._labor_minute_rate('filing')
        setting_rate = self._labor_minute_rate('setting')

        filing_cost = self._model_labor_cost('FIL')
        setting_cost = sum(
            (line.setting or 0.0) * (line.pieces or 1)
            for line in (product.stone_line_ids if product else [])
        )

        stones = []
        if product:
            for line in product.stone_line_ids:
                stone = line.stone_id
                recut_shape = (line.reshaped_shape_id.code
                               if line.reshaped_shape_id
                               else (stone.shape_id.code if stone.shape_id else ''))
                recut_size = (line.reshaped_size_id.name
                              if line.reshaped_size_id
                              else (stone.size_id.name if stone.size_id else ''))
                stones.append({
                    'code': stone.code if stone else '',
                    'pieces': line.pieces,
                    'weight': line.weight,
                    'recut_shape': recut_shape,
                    'recut_size': recut_size,
                })

        parts = []
        if product:
            for part_line in product.part_ids:
                parts.append({
                    'code': part_line.part_id.code if part_line.part_id else '',
                    'name': part_line.part_id.name if part_line.part_id else '',
                    'quantity': part_line.quantity,
                })
        if not parts:
            # Legacy cards always list at least the model itself as the
            # single sub part ('P720 # 1').
            parts = [{'code': self.model_code or '', 'name': '',
                      'quantity': int(self.qty) or 1}]

        image = False
        if product:
            if product.model_id and product.model_id.picture_image:
                image = product.model_id.picture_image
            elif product.image_1920:
                image = product.image_1920
        if isinstance(image, str):
            # QWeb's image_data_uri expects base64 bytes
            image = image.encode()

        metal_letter = self._metal_letter()
        tag = self.tag or (item.special_instruction if item else '') or ''

        # Header center: the legacy '#PO EMPLOYEE MODE DATE' line is stored
        # verbatim in the item group; compose a fallback from the document.
        if item and item.item_group:
            header_center = item.item_group
        else:
            po = sis.customer_po or ''
            if po and not po.startswith('#'):
                po = '#' + po
            header_center = ' '.join(filter(None, [
                po,
                sis.employee or '',
                (sis.rcv_mode_id.name or '').upper() if sis.rcv_mode_id else '',
                sis.date_created.strftime('%d/%m/%Y')
                if sis.date_created else '',
            ]))

        # Corner: client code of the reference + market code of the tag
        # ('SO-EMA-25001' + '(IL) ...' -> 'EMA+IL').
        name_parts = (doc.name or '').split('-')
        client_code = name_parts[1] if len(name_parts) >= 3 else (
            sis.party_code or '')
        market = re.match(r'^\((\w+)\)', tag)
        corner_ref = client_code + ('+%s' % market.group(1) if market else '')

        return {
            'barcode': self.name,
            'barcode_url': self.barcode_image_url(),
            'model_code': self.model_code or '',
            'design': self.design or '',
            'qty': int(self.qty) if self.qty == int(self.qty or 0) else self.qty,
            'tag': tag,
            'size': self.size or '',
            'header_center': header_center,
            'corner_ref': corner_ref,
            'customer_po': sis.customer_po or '',
            'employee': sis.employee or '',
            'rcv_mode': (sis.rcv_mode_id.name or '').upper() if sis.rcv_mode_id else '',
            'order_no': sis.legacy_id or '',
            'so_name': sis.name or '',
            'order_date': sis.date_created,
            'delivery_date': sis.date_due,
            'gold_weight': self._gold_weight(),
            'filing_weight': '',
            'filing_min': round(filing_cost / filing_rate, 2)
                          if filing_cost else '',
            'setting_min': round(setting_cost / setting_rate, 2)
                           if setting_cost else '',
            'metal_letter': metal_letter,
            'purity': self.purity or '',
            'stamp_color': METAL_STAMP_COLORS.get(metal_letter, '#ffffff'),
            'stones': stones,
            'parts': parts,
            'image': image,
        }
