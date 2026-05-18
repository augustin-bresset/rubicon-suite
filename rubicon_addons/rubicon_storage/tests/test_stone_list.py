# rubicon_addons/rubicon_storage/tests/test_stone_list.py
from odoo.tests import common, tagged


def _get_or_create(env, model, domain, vals):
    rec = env[model].search(domain, limit=1)
    if not rec:
        rec = env[model].create(vals)
    return rec


@tagged('post_install', '-at_install')
class TestStoneList(common.TransactionCase):

    def setUp(self):
        super().setUp()
        # Stone taxonomy — search by the actual unique field to avoid constraint errors
        self.type1 = _get_or_create(
            self.env, 'pdp.stone.type', [('code', '=', 'AME')],
            {'code': 'AME', 'name': 'Amethyst'})
        self.shape1 = _get_or_create(
            self.env, 'pdp.stone.shape', [('shape', '=', 'Round')],
            {'code': 'RND', 'shape': 'Round'})
        self.shade1 = _get_or_create(
            self.env, 'pdp.stone.shade', [('shade', '=', 'A Light Color')],
            {'code': 'ALC', 'shade': 'A Light Color'})
        self.size1 = _get_or_create(
            self.env, 'pdp.stone.size', [('name', '=', '2.2')],
            {'name': '2.2'})
        self.size2 = _get_or_create(
            self.env, 'pdp.stone.size', [('name', '=', '2.9')],
            {'name': '2.9'})

        # pdp.stone records — search by tuple (unique constraint) to avoid duplicates
        self.stone1 = _get_or_create(
            self.env, 'pdp.stone',
            [('type_id', '=', self.type1.id), ('shape_id', '=', self.shape1.id),
             ('shade_id', '=', self.shade1.id), ('size_id', '=', self.size1.id)],
            {
                'code': 'AME-ALC-RND-22',
                'type_id': self.type1.id,
                'shape_id': self.shape1.id,
                'shade_id': self.shade1.id,
                'size_id': self.size1.id,
            })
        self.stone2 = _get_or_create(
            self.env, 'pdp.stone',
            [('type_id', '=', self.type1.id), ('shape_id', '=', self.shape1.id),
             ('shade_id', '=', self.shade1.id), ('size_id', '=', self.size2.id)],
            {
                'code': 'AME-ALC-RND-29',
                'type_id': self.type1.id,
                'shape_id': self.shape1.id,
                'shade_id': self.shade1.id,
                'size_id': self.size2.id,
            })

        # Composition with two lines
        self.comp = self.env['pdp.product.stone.composition'].create({'code': 'COMP-TEST'})
        self.line1 = self.env['pdp.product.stone'].create({
            'composition_id': self.comp.id,
            'stone_id': self.stone1.id,
            'pieces': 2,
            'weight': 0.5,
        })
        self.line2 = self.env['pdp.product.stone'].create({
            'composition_id': self.comp.id,
            'stone_id': self.stone2.id,
            'pieces': 1,
            'weight': 0.7,
        })

        # Product linked to composition
        model = self.env['pdp.product.model'].create({'code': 'M-TEST-RS'})
        self.product = self.env['pdp.product'].create({
            'model_id': model.id,
            'code': 'PROD-TEST-RS',
            'stone_composition_id': self.comp.id,
        })

        # SIS document (Sale Order) in 2025
        self.doc = self.env['sis.document'].create({
            'name': 'SO-TEST-25001',
            'doc_type_code': 'SO',
            'date_created': '2025-06-15',
        })
        self.env['sis.document.item'].create({
            'document_id': self.doc.id,
            'design': 'PROD-TEST-RS',
            'product_id': self.product.id,
            'qty': 1,
        })

    def test_get_available_years_includes_2025(self):
        years = self.env['sis.document'].get_available_years()
        self.assertIn(2025, years)

    def test_get_sale_orders_by_year(self):
        orders = self.env['sis.document'].get_sale_orders_by_year(2025)
        names = [o['name'] for o in orders]
        self.assertIn('SO-TEST-25001', names)

    def test_get_sale_orders_by_year_excludes_other_years(self):
        orders = self.env['sis.document'].get_sale_orders_by_year(2020)
        names = [o['name'] for o in orders]
        self.assertNotIn('SO-TEST-25001', names)

    def test_get_stone_list_grouped_default(self):
        rows = self.env['sis.document'].get_stone_list(self.doc.id)
        self.assertEqual(len(rows), 2)
        types = [r['type'] for r in rows]
        self.assertEqual(types.count('Amethyst'), 2)
        # Each row has no 'product' key in grouped mode
        self.assertNotIn('product', rows[0])

    def test_get_stone_list_grouped_sums_pcs(self):
        # Add second item with same product (same composition → same stones)
        model2 = self.env['pdp.product.model'].create({'code': 'M-TEST-RS2'})
        product2 = self.env['pdp.product'].create({
            'model_id': model2.id,
            'code': 'PROD-TEST-RS2',
            'stone_composition_id': self.comp.id,
        })
        self.env['sis.document.item'].create({
            'document_id': self.doc.id,
            'design': 'PROD-TEST-RS2',
            'product_id': product2.id,
            'qty': 1,
        })
        rows = self.env['sis.document'].get_stone_list(self.doc.id, grouped=True)
        # stone1 (size 2.2) appears twice → pcs should be 4 (2+2)
        row_22 = next(r for r in rows if r['size'] == '2.2')
        self.assertEqual(row_22['pcs'], 4)

    def test_get_stone_list_ungrouped_has_product(self):
        rows = self.env['sis.document'].get_stone_list(self.doc.id, grouped=False)
        self.assertEqual(len(rows), 2)
        self.assertIn('product', rows[0])
        self.assertEqual(rows[0]['product'], 'PROD-TEST-RS')

    def test_get_stone_list_skips_items_without_product(self):
        self.env['sis.document.item'].create({
            'document_id': self.doc.id,
            'design': 'NO-PRODUCT',
            'qty': 1,
        })
        rows = self.env['sis.document'].get_stone_list(self.doc.id)
        self.assertEqual(len(rows), 2)  # unchanged

    def test_get_stones_for_report(self):
        rows = self.doc.get_stones_for_report()
        self.assertEqual(len(rows), 2)
        self.assertIn('type', rows[0])
        self.assertIn('pcs', rows[0])
