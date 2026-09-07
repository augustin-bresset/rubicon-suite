from PIL import Image as PILImage

from odoo.tests.common import TransactionCase
from odoo.tools.image import image_to_base64

# A real 1x1 PNG: the Image fields and report_picture() run it through PIL.
TINY_PNG = image_to_base64(PILImage.new('RGB', (1, 1), 'white'), 'PNG')


class TestReportHelpers(TransactionCase):
    """Printed-document helpers: design lines and the optional line picture."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.doc = cls.env['sis.document'].create(
            {'name': 'SQ-ZZH-1', 'doc_type_code': 'SQ'})
        cls.item = cls.env['sis.document.item'].create({
            'document_id': cls.doc.id, 'design': 'ZZH1-AM/W', 'qty': 1,
        })

    def test_design_lines_default_to_the_snapshot(self):
        self.assertEqual(self.item.report_design_lines(), ['ZZH1-AM/W'])

    def test_design_lines_survive_an_empty_design(self):
        item = self.env['sis.document.item'].create(
            {'document_id': self.doc.id, 'qty': 1})
        self.assertEqual(item.report_design_lines(), [''])

    def test_picture_absent_without_a_product(self):
        self.assertFalse(self.item.report_picture())

    def test_picture_resolves_through_the_linked_product(self):
        # pdp_picture is a soft dependency of the report; only testable when
        # it is installed (always the case in the combined CI database).
        if 'pdp.picture' not in self.env:
            self.skipTest('pdp_picture is not installed')
        model = self.env['pdp.product.model'].create({'code': 'ZZH1'})
        product = self.env['pdp.product'].create({
            'code': 'ZZH1-AM/W', 'model_id': model.id, 'metal': 'W',
            'active': True})
        self.env['pdp.picture'].create({
            'scope': 'product', 'product_ids': [(6, 0, product.ids)],
            'image_1920': TINY_PNG,
        })
        item = self.env['sis.document.item'].create({
            'document_id': self.doc.id, 'design': 'ZZH1-AM/W', 'qty': 1,
        })
        self.assertEqual(item.product_id, product)
        self.assertTrue(item.report_picture())
