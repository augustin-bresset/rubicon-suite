from odoo import models, fields


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

    def action_print_pdf(self):
        return self.env.ref('sis_document.action_report_sis_document').report_action(self)
