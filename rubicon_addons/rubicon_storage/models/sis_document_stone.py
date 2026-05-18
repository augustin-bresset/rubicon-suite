# rubicon_addons/rubicon_storage/models/sis_document_stone.py
from odoo import models, api


class SisDocument(models.Model):
    _inherit = 'sis.document'

    @api.model
    def get_available_years(self):
        self.env.cr.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM date_created)::int AS yr
            FROM sis_document
            WHERE doc_type_code = 'SO' AND date_created IS NOT NULL
            ORDER BY yr DESC
        """)
        return [row[0] for row in self.env.cr.fetchall()]

    @api.model
    def get_sale_orders_by_year(self, year):
        docs = self.search([
            ('doc_type_code', '=', 'SO'),
            ('date_created', '>=', f'{year}-01-01'),
            ('date_created', '<=', f'{year}-12-31'),
        ], order='name')
        return [{'id': d.id, 'name': d.name} for d in docs]

    @api.model
    def get_stone_list(self, document_id, grouped=True):
        doc = self.browse(document_id)
        return doc._extract_stone_lines(grouped)

    def action_print_stone_list(self):
        self.ensure_one()
        return self.env.ref('rubicon_storage.action_report_stone_list').report_action(self)

    def get_stones_for_report(self):
        self.ensure_one()
        return self._extract_stone_lines(grouped=True)

    def _extract_stone_lines(self, grouped=True):
        rows = []
        for item in self.item_ids:
            product = item.product_id
            if not product or not product.stone_composition_id:
                continue
            for line in product.stone_composition_id.stone_line_ids:
                stone = line.stone_id
                rows.append({
                    'product': product.code or '',
                    'type': stone.type_id.name if stone.type_id else '',
                    'shape': stone.shape_id.shape if stone.shape_id else '',
                    'shade': stone.shade_id.shade if stone.shade_id else '',
                    'size': stone.size_id.name if stone.size_id else '',
                    'weight': line.weight,
                    'pcs': line.pieces,
                })

        if not grouped:
            return sorted(rows, key=lambda r: (r['product'], r['type'], r['shape'], r['shade'], r['size']))

        agg = {}
        for r in rows:
            key = (r['type'], r['shape'], r['shade'], r['size'])
            if key in agg:
                agg[key]['pcs'] += r['pcs']
            else:
                agg[key] = {
                    'type': r['type'],
                    'shape': r['shape'],
                    'shade': r['shade'],
                    'size': r['size'],
                    'weight': r['weight'],
                    'pcs': r['pcs'],
                }
        return sorted(agg.values(), key=lambda r: (r['type'], r['shape'], r['shade'], r['size']))
