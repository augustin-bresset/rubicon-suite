from odoo import models, fields, api


class SisDocument(models.Model):
    _name = 'sis.document'
    _description = 'SIS Sales Document'
    _rec_name = 'name'
    _order = 'date_created desc, id desc'

    # Header
    name = fields.Char(string='Doc Name', required=True, index=True)
    doc_type_id = fields.Many2one('sis.doc.type', string='Document Type')
    doc_type_code = fields.Char(string='Doc Type Code', index=True)
    legacy_id = fields.Integer(string='Legacy ID', index=True)

    # Status
    closed = fields.Boolean(default=False)
    canceled = fields.Boolean(default=False)

    # Dates
    date_created = fields.Date(string='Created')
    date_due = fields.Date(string='Due Date')

    # Party
    party_id = fields.Many2one('res.partner', string='Customer')
    party_code = fields.Char(string='Customer Code')

    # General
    margin_id = fields.Many2one('pdp.margin', string='Margin')
    margin_name = fields.Char(string='Margin Name')
    currency_id = fields.Many2one('res.currency', string='Currency')
    currency_legacy = fields.Char(string='Currency (legacy)')  # preserve original
    notes = fields.Text()
    footnotes = fields.Text()

    # Payment
    pay_term_id = fields.Many2one('sis.pay.term', string='Payment Term')

    # Order specific
    customer_po = fields.Char(string='Customer P.O. No.')
    rcv_mode_id = fields.Many2one('sis.doc.in.mode', string='Receiving Mode')
    trade_fair_id = fields.Many2one('sis.trade.fair', string='Trade Fair')
    employee = fields.Char()

    # Shipment
    ship_address = fields.Text(string='Ship To Address')
    ship_method_id = fields.Many2one('sis.shipper', string='Ship Method')
    ship_consignee_bank = fields.Boolean(string='Consignee Bank')
    ship_for_acc_of = fields.Char(string='For Account Of')
    ship_book = fields.Char(string='Book')
    ship_page = fields.Char(string='Page')

    # Financials (computed in legacy, stored here for import)
    total_fob = fields.Float(string='Total F.O.B', digits=(12, 2))
    freight_insurance = fields.Float(string='Freight & Insurance', digits=(12, 2))
    total_cif = fields.Float(string='Total C.I.F', digits=(12, 2))
    deposit = fields.Float(string='Less Deposit', digits=(12, 2))
    total_amount = fields.Float(string='Total Amount', digits=(12, 2))
    total_qty = fields.Integer(string='Total Qty')
    total_cost = fields.Float(string='Total Cost', digits=(12, 2))
    total_profit = fields.Float(string='Total Profit', digits=(12, 2))
    profit_pct = fields.Float(string='Profit %', digits=(6, 2))

    # Company info stamp
    stamp = fields.Text(string='Stamp')

    # Items
    item_ids = fields.One2many('sis.document.item', 'document_id', string='Items')

    # Child documents
    child_doc_ids = fields.Many2many(
        'sis.document', 'sis_doc_parent_child_rel',
        'parent_id', 'child_id', string='Child Documents')

    def get_ornament_quantities(self):
        """Return {category_name: total_qty} grouped by product category."""
        counts = {}
        for item in self.item_ids:
            cat_name = item.get_category_name() or 'Other'
            counts[cat_name] = counts.get(cat_name, 0) + int(item.qty)
        return counts

    def action_print_pdf(self):
        return self.env.ref('sis_document.action_report_sis_document').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get('name', '')
            parts = name.split('-')
            # Partial prefix: "SO-EMA-" → ['SO', 'EMA', '']
            if len(parts) == 3 and parts[2] == '':
                doc_type, client_code = parts[0], parts[1]
                date = vals.get('date_created') or fields.Date.today()
                # date arrives as string "2025-01-15" via JSON-RPC
                if isinstance(date, str):
                    yy = date[2:4]
                else:
                    yy = str(date.year)[2:]
                prefix = f'{doc_type}-{client_code}-{yy}'
                self.env.cr.execute(
                    "SELECT MAX(name) FROM sis_document WHERE name LIKE %s",
                    [prefix + '%']
                )
                row = self.env.cr.fetchone()
                last = row[0] if row and row[0] else None
                seq = (int(last[len(prefix):]) + 1) if last else 1
                vals['name'] = f'{prefix}{seq:03d}'
                vals['doc_type_code'] = doc_type
        return super().create(vals_list)
