import base64
import io
from datetime import date

from odoo import api, fields, models


class PdpToolsService(models.AbstractModel):
    _name = 'pdp.tools.service'
    _description = 'PDP Tools Service (Reports & Check Data)'

    # =========================================================================
    # Excel Report Generation
    # =========================================================================

    @api.model
    def generate_report_excel(self, report_types, params):
        """
        Generate an Excel workbook with one sheet per selected report type.

        Args:
            report_types: list of str — subset of
                ['price_list', 'pictures', 'item_by_date', 'item_by_stone']
            params: dict with keys:
                margin_id, purity_id, metal_id, currency_id,
                price_list_type ('single'|'multi'),
                category_id, from_seq, till_seq,
                updated_date, appl_from_date,
                items ('all'|'in_collection')

        Returns:
            {'filename': str, 'data': base64_str}
        """
        try:
            import xlsxwriter
        except ImportError:
            return {'error': 'xlsxwriter is not installed'}

        buf = io.BytesIO()
        workbook = xlsxwriter.Workbook(buf, {'in_memory': True})

        # ── Styles ────────────────────────────────────────────────────────────
        hdr = workbook.add_format({
            'bold': True, 'bg_color': '#2D5F8A', 'font_color': 'white',
            'border': 1, 'text_wrap': True,
        })
        cell = workbook.add_format({'border': 1, 'text_wrap': False})
        money = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        date_fmt = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})
        title = workbook.add_format({'bold': True, 'font_size': 13})

        # ── Resolve lookup records ────────────────────────────────────────────
        margin = (
            self.env['pdp.margin'].browse(params.get('margin_id'))
            if params.get('margin_id') else
            self.env['pdp.margin'].search([], limit=1)
        )
        currency = (
            self.env['res.currency'].browse(params.get('currency_id'))
            if params.get('currency_id') else
            self.env.company.currency_id
        )

        # ── Build product domain ──────────────────────────────────────────────
        domain = [('active', '=', True)]
        if params.get('category_id'):
            domain.append(('model_id.category_id', '=', params['category_id']))
        if params.get('items') == 'in_collection':
            domain.append(('in_collection', '=', True))

        all_products = self.env['pdp.product'].search(domain, order='code')

        # from_seq / till_seq: slice the ordered product list (1-based index)
        from_s = max(0, int(params.get('from_seq', 0)))
        till_s = int(params.get('till_seq', 100))
        if from_s > 0 or till_s < len(all_products):
            products = all_products[from_s:till_s]
        else:
            products = all_products

        today = fields.Date.context_today(self)

        # ── Sheets ────────────────────────────────────────────────────────────
        if 'price_list' in report_types:
            self._sheet_price_list(workbook, hdr, cell, money, title, products, margin, currency, today)

        if 'item_by_date' in report_types:
            self._sheet_item_by_date(workbook, hdr, cell, date_fmt, title, products)

        if 'item_by_stone' in report_types:
            self._sheet_item_by_stone(workbook, hdr, cell, title, products)

        if 'pictures' in report_types:
            self._sheet_pictures(workbook, hdr, cell, title, products)

        if not report_types:
            ws = workbook.add_worksheet('Empty')
            ws.write(0, 0, 'No report type selected.', title)

        workbook.close()
        buf.seek(0)
        data = base64.b64encode(buf.read()).decode('utf-8')
        return {'filename': 'pdp_report.xlsx', 'data': data}

    # ── Individual sheet builders ─────────────────────────────────────────────

    def _sheet_price_list(self, wb, hdr, cell, money, title, products, margin, currency, today):
        ws = wb.add_worksheet('Price List')
        ws.set_column(0, 0, 14)
        ws.set_column(1, 1, 18)
        ws.set_column(2, 5, 12)

        ws.write(0, 0, 'Price List', title)
        ws.write(1, 0, f'Margin: {margin.code if margin else "—"}   Currency: {currency.name}')

        cols = ['Code', 'Model', 'Category', 'Metal', 'Cost', 'Margin', 'Price']
        for c, label in enumerate(cols):
            ws.write(3, c, label, hdr)

        row = 4
        for product in products:
            try:
                result = self.env['pdp.price.service'].compute_product_price(
                    product=product, margin=margin, currency=currency, date=today
                )
                totals = result.get('totals', {})
                cost   = totals.get('cost', 0.0)
                marg   = totals.get('margin', 0.0)
                price  = totals.get('price', 0.0)
            except Exception:
                cost = marg = price = 0.0

            cat = product.model_id.category_id.code if product.model_id.category_id else ''
            ws.write(row, 0, product.code or '', cell)
            ws.write(row, 1, product.model_id.code if product.model_id else '', cell)
            ws.write(row, 2, cat, cell)
            ws.write(row, 3, product.metal or '', cell)
            ws.write_number(row, 4, cost, money)
            ws.write_number(row, 5, marg, money)
            ws.write_number(row, 6, price, money)
            row += 1

    def _sheet_item_by_date(self, wb, hdr, cell, date_fmt, title, products):
        ws = wb.add_worksheet('Item List by Date')
        ws.set_column(0, 0, 14)
        ws.set_column(1, 1, 18)
        ws.set_column(2, 2, 16)
        ws.set_column(3, 4, 14)

        ws.write(0, 0, 'Item List by Date', title)

        cols = ['Code', 'Model', 'Category', 'Created', 'Active', 'In Collection']
        for c, label in enumerate(cols):
            ws.write(2, c, label, hdr)

        row = 3
        for product in products.sorted(key=lambda p: p.create_date or date(1970, 1, 1)):
            cat = product.model_id.category_id.code if product.model_id.category_id else ''
            created = product.create_date.date() if product.create_date else ''
            ws.write(row, 0, product.code or '', cell)
            ws.write(row, 1, product.model_id.code if product.model_id else '', cell)
            ws.write(row, 2, cat, cell)
            ws.write(row, 3, str(created), cell)
            ws.write(row, 4, 'Yes' if product.active else 'No', cell)
            ws.write(row, 5, 'Yes' if product.in_collection else 'No', cell)
            row += 1

    def _sheet_item_by_stone(self, wb, hdr, cell, title, products):
        ws = wb.add_worksheet('Item List by Stone')
        ws.set_column(0, 0, 14)
        ws.set_column(1, 3, 12)
        ws.set_column(4, 4, 50)

        ws.write(0, 0, 'Item List by Stone', title)

        cols = ['Stone Code', 'Type', 'Shape', 'Size', 'Used in Products']
        for c, label in enumerate(cols):
            ws.write(2, c, label, hdr)

        # Build stone → product mapping
        stone_products = {}  # stone_id → {'stone': record, 'products': [code, ...]}
        for product in products:
            if not product.stone_composition_id:
                continue
            for line in product.stone_composition_id.stone_line_ids:
                if not line.stone_id:
                    continue
                sid = line.stone_id.id
                if sid not in stone_products:
                    stone_products[sid] = {'stone': line.stone_id, 'products': set()}
                stone_products[sid]['products'].add(product.code)

        row = 3
        for sid, info in sorted(stone_products.items(), key=lambda x: x[1]['stone'].code or ''):
            s = info['stone']
            ws.write(row, 0, s.code or '', cell)
            ws.write(row, 1, s.type_id.name if s.type_id else '', cell)
            ws.write(row, 2, s.shape_id.shape if s.shape_id else '', cell)
            ws.write(row, 3, s.size_id.name if s.size_id else '', cell)
            ws.write(row, 4, ', '.join(sorted(info['products'])), cell)
            row += 1

    def _sheet_pictures(self, wb, hdr, cell, title, products):
        ws = wb.add_worksheet('Pictures')
        ws.set_column(0, 0, 14)
        ws.set_column(1, 1, 18)
        ws.set_column(2, 2, 12)

        ws.write(0, 0, 'Pictures', title)

        cols = ['Code', 'Model', 'Photo Count']
        for c, label in enumerate(cols):
            ws.write(2, c, label, hdr)

        row = 3
        for product in products:
            pic_count = self.env['pdp.picture'].search_count([
                ('product_ids', 'in', [product.id])
            ])
            ws.write(row, 0, product.code or '', cell)
            ws.write(row, 1, product.model_id.code if product.model_id else '', cell)
            ws.write_number(row, 2, pic_count, cell)
            row += 1

    # =========================================================================
    # Check Data Queries
    # =========================================================================

    @api.model
    def get_check_data(self, check_type):
        """
        Returns list of dicts: [{stone_code, description, used_in}, ...]
        check_type: 'blank_stone_costs' | 'blank_stone_weights' | 'blank_stone_margins'
        """
        if check_type == 'blank_stone_costs':
            return self._check_blank_stone_costs()
        elif check_type == 'blank_stone_weights':
            return self._check_blank_stone_weights()
        elif check_type == 'blank_stone_margins':
            return self._check_blank_stone_margins()
        return []

    def _check_blank_stone_costs(self):
        """Stones used in products that have no cost set."""
        # Get all stones actually used in products
        used_stone_ids = self.env['pdp.product.stone'].search([]).mapped('stone_id').ids
        if not used_stone_ids:
            return []
        stones = self.env['pdp.stone'].search([
            ('id', 'in', used_stone_ids),
            '|', ('cost', '=', False), ('cost', '=', 0),
        ])
        return self._stones_to_result(stones)

    def _check_blank_stone_weights(self):
        """Product stone lines where weight is 0 or missing."""
        lines = self.env['pdp.product.stone'].search([
            '|', ('weight', '=', False), ('weight', '=', 0)
        ])
        # Group by stone_id
        stone_products = {}
        for line in lines:
            if not line.stone_id:
                continue
            sid = line.stone_id.id
            if sid not in stone_products:
                stone_products[sid] = {'stone': line.stone_id, 'products': set()}
            comp = line.composition_id
            # find products linked to this composition
            products = self.env['pdp.product'].search([('stone_composition_id', '=', comp.id)])
            for p in products:
                stone_products[sid]['products'].add(p.code)

        results = []
        for sid, info in sorted(stone_products.items(), key=lambda x: x[1]['stone'].code or ''):
            s = info['stone']
            results.append({
                'stone_code': s.code or '',
                'description': self._stone_description(s),
                'used_in': ', '.join(sorted(info['products'])),
            })
        return results

    def _check_blank_stone_margins(self):
        """
        Stones used in products whose type is not covered by any pdp.margin.stone entry,
        AND whose category is not covered by any pdp.margin.stone.conditional entry.
        """
        # Stone types covered by at least one normal margin
        covered_type_ids = set(
            self.env['pdp.margin.stone'].search([]).mapped('stone_type_id').ids
        )
        # Stone categories covered by at least one conditional margin
        covered_cat_ids = set(
            self.env['pdp.margin.stone.conditional'].search([]).mapped('stone_cat_id').ids
        )

        used_stone_ids = self.env['pdp.product.stone'].search([]).mapped('stone_id').ids
        if not used_stone_ids:
            return []

        stones = self.env['pdp.stone'].search([('id', 'in', used_stone_ids)])
        uncovered = stones.filtered(
            lambda s: (s.type_id.id not in covered_type_ids)
            and (not s.type_id.category_id or s.type_id.category_id.id not in covered_cat_ids)
        )
        return self._stones_to_result(uncovered)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _stone_description(self, stone):
        parts = []
        if stone.type_id:
            parts.append(stone.type_id.name)
        if stone.shape_id:
            parts.append(stone.shape_id.shape)
        if stone.size_id:
            parts.append(stone.size_id.name)
        return ' / '.join(parts) if parts else ''

    def _stones_to_result(self, stones):
        """For a set of stones, return result list with product usage."""
        if not stones:
            return []
        # Build stone → product map
        all_lines = self.env['pdp.product.stone'].search([('stone_id', 'in', stones.ids)])
        stone_products = {s.id: set() for s in stones}
        for line in all_lines:
            if line.stone_id.id not in stone_products:
                continue
            prods = self.env['pdp.product'].search([('stone_composition_id', '=', line.composition_id.id)])
            for p in prods:
                stone_products[line.stone_id.id].add(p.code)

        results = []
        for stone in stones.sorted(key=lambda s: s.code or ''):
            results.append({
                'stone_code': stone.code or '',
                'description': self._stone_description(stone),
                'used_in': ', '.join(sorted(stone_products.get(stone.id, set()))),
            })
        return results
