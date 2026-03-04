from odoo import models, fields


class SisDocumentItem(models.Model):
    _name = 'sis.document.item'
    _description = 'SIS Document Line Item'
    _rec_name = 'design'

    document_id = fields.Many2one('sis.document', string='Document', required=True,
                                   ondelete='cascade', index=True)

    # Design reference (MODEL-COLORS/M)
    design = fields.Char(string='Design', index=True)
    product_id = fields.Many2one('pdp.product', string='PDP Product',
                                 index=True, ondelete='set null')
    model_code = fields.Char(string='Model')
    product_code = fields.Char(string='Product Code')
    color_code = fields.Char(string='Colors')
    metal_code = fields.Char(string='Metal')
    purity = fields.Char(string='Purity')
    description = fields.Text()

    # Quantities
    qty = fields.Float(string='Qty', digits=(10, 1))
    qty_shipped = fields.Float(string='Qty Shipped', digits=(10, 1))
    qty_balance = fields.Float(string='Qty Balance', digits=(10, 1))

    # Pricing
    currency_id = fields.Many2one('res.currency', string='Currency')
    currency_legacy = fields.Char(string='Currency (legacy)')  # preserve original
    unit_price = fields.Float(string='Unit Price', digits=(12, 2))
    amount = fields.Float(string='Amount', digits=(12, 2))
    unit_cost = fields.Float(string='Unit Cost', digits=(12, 2))
    cost = fields.Float(string='Cost', digits=(12, 2))
    profit = fields.Float(string='Profit', digits=(12, 2))
    profit_pct = fields.Float(string='Profit %', digits=(6, 4))

    # Weights
    diamond_weight = fields.Float(string='Diamond Wt.', digits=(10, 4))
    stone_weight = fields.Float(string='Stone Wt.', digits=(10, 4))
    diverse_weight = fields.Float(string='Diverse Wt.', digits=(10, 4))
    metal_weight = fields.Float(string='Metal Wt.', digits=(10, 4))

    # Instructions / Sizes
    item_group = fields.Char(string='Item Group')
    special_instruction = fields.Text(string='Special Instruction')
    size_remarks = fields.Char(string='Size Remarks')

    # Reference to source document (for copy/child tracking)
    ref_document = fields.Char(string='Ref. Document')

    # Sequence within document
    sequence = fields.Integer(string='Seq', default=0)
