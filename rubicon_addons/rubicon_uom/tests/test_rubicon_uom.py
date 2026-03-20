from odoo.tests.common import TransactionCase


class TestRubiconUomCategory(TransactionCase):

    def test_create_category(self):
        cat = self.env['rubicon.uom.category'].create({
            'name': 'Test Weight',
            'code': 'test_weight',
        })
        self.assertEqual(cat.code, 'test_weight')
        # _rec_name='code' means display_name == code value
        self.assertEqual(cat.display_name, 'test_weight')

    def test_code_unique(self):
        self.env['rubicon.uom.category'].create({'name': 'A', 'code': 'unique_test'})
        with self.assertRaises(Exception):
            self.env['rubicon.uom.category'].create({'name': 'B', 'code': 'unique_test'})
