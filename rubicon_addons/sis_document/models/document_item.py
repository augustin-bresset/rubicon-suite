import base64

from odoo import models, fields, api
from odoo.tools import image_process


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
    amount = fields.Float(string='Amount', digits=(12, 2),
                          compute='_compute_amounts', store=True)
    unit_cost = fields.Float(string='Unit Cost', digits=(12, 2))
    cost = fields.Float(string='Cost', digits=(12, 2),
                        compute='_compute_amounts', store=True)
    profit = fields.Float(string='Profit', digits=(12, 2),
                          compute='_compute_amounts', store=True)
    profit_pct = fields.Float(string='Profit %', digits=(6, 4),
                              compute='_compute_amounts', store=True)

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

    @api.depends('qty', 'unit_price', 'unit_cost')
    def _compute_amounts(self):
        # Frozen inputs are unit_price / unit_cost; the line rollups derive from
        # them, with the same formulas as the legacy import (profit% = profit / cost).
        for item in self:
            item.amount = (item.qty or 0.0) * (item.unit_price or 0.0)
            item.cost = (item.qty or 0.0) * (item.unit_cost or 0.0)
            item.profit = item.amount - item.cost
            item.profit_pct = (item.profit / item.cost) if item.cost else 0.0

    # =========================================================================
    # Product linking — keep the product_id FK in sync with the design code
    #
    # 'design' is the historical snapshot of what was ordered and equals
    # pdp.product.code. The FK lets callers use the stable product id instead
    # of re-matching the string, so products can later be renamed without
    # breaking documents. product_id is fully server-derived: the client never
    # sends it, it is resolved here from 'design'.
    # =========================================================================

    @api.model
    def _resolve_product_ids(self, designs):
        """Map design strings to pdp.product ids.

        A design is matched against the current product code first and, for
        designs still unresolved, falls back to the legacy code preserved when
        a product's code was migrated to the structured colour code. The design
        snapshots hold the original (legacy) code, so this fallback keeps them
        linked after products are renamed.

        Includes archived products (active_test=False); most legacy products
        are archived. When several products share a code (codes are not unique
        until the colour-code migration), the active one with the lowest id
        wins, deterministically.
        """
        designs = {d for d in designs if d}
        if not designs:
            return {}
        Product = self.env['pdp.product'].with_context(active_test=False)
        mapping = {}
        # Primary match: the design equals the product's current code.
        for product in Product.search(
            [('code', 'in', list(designs))], order='active desc, id'
        ):
            mapping.setdefault(product.code, product.id)
        # Fallback: for designs no current code resolved, match the legacy code
        # kept when the product was renamed to the structured colour code.
        remaining = designs - set(mapping)
        if remaining:
            for product in Product.search(
                [('legacy_code', 'in', list(remaining))], order='active desc, id'
            ):
                mapping.setdefault(product.legacy_code, product.id)
        return mapping

    @api.model_create_multi
    def create(self, vals_list):
        to_resolve = [
            v['design'] for v in vals_list
            if v.get('design') and not v.get('product_id')
        ]
        if to_resolve:
            mapping = self._resolve_product_ids(to_resolve)
            for vals in vals_list:
                if vals.get('design') and not vals.get('product_id'):
                    product_id = mapping.get(vals['design'])
                    if product_id:
                        vals['product_id'] = product_id
        return super().create(vals_list)

    def write(self, vals):
        # Re-link whenever the design changes, unless an explicit product_id is
        # provided. Clears the FK when the new design matches no product.
        if 'design' in vals and 'product_id' not in vals:
            design = vals.get('design')
            mapping = self._resolve_product_ids([design]) if design else {}
            vals = dict(vals, product_id=mapping.get(design) or False)
        return super().write(vals)

    @api.model
    def _backfill_product_links(self):
        """Link items to products by design==code where product_id is empty.

        Idempotent: only touches still-unlinked items. Returns
        ``{'linked': n, 'unmatched': m}``.
        """
        items = self.search([('product_id', '=', False), ('design', '!=', False)])
        mapping = self._resolve_product_ids(items.mapped('design'))
        by_product = {}
        for item in items:
            product_id = mapping.get(item.design)
            if product_id:
                by_product.setdefault(product_id, []).append(item.id)
        linked = 0
        for product_id, item_ids in by_product.items():
            self.browse(item_ids).write({'product_id': product_id})
            linked += len(item_ids)
        return {'linked': linked, 'unmatched': len(items) - linked}

    def get_category_name(self):
        """Return the product category name from the design code alphabetic prefix."""
        self.ensure_one()
        prefix = ''
        for ch in (self.design or ''):
            if ch.isalpha():
                prefix += ch
            else:
                break
        if not prefix:
            return ''
        cat = self.env['pdp.product.category'].sudo().search([('code', '=', prefix)], limit=1)
        return cat.name if cat else ''

    # =========================================================================
    # Printed document helpers (called from the QWeb report)
    # =========================================================================

    def report_design_lines(self):
        """Design reference lines to print for this item, first line prominent.

        Base behaviour: the historical design snapshot only. Notation modules
        extend this to honour the ``print_notation`` context key.
        """
        self.ensure_one()
        return [self.design or '']

    def report_picture(self, size=256):
        """Picture (base64) to print next to this line, or False.

        Sourced from pdp.picture through the linked product. pdp_picture is
        optional, so its model is looked up at runtime rather than through a
        manifest dependency. A product-scoped picture wins over the shared
        model thumbnail; the image is downscaled so long documents stay
        printable.
        """
        self.ensure_one()
        if 'pdp.picture' not in self.env or not self.product_id:
            return False
        picture = self.env['pdp.picture'].search(
            [('product_ids', 'in', self.product_id.id)],
            order='scope desc, id', limit=1,
        )
        if not picture.image_1920:
            return False
        raw = image_process(base64.b64decode(picture.image_1920), size=(size, size))
        return base64.b64encode(raw) if raw else False
