from odoo.tests.common import TransactionCase


class TestPsUtilities(TransactionCase):
    """Backend helpers behind the two PSUtilities screens."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.U = cls.env['ps.utilities']

        # PDP fixtures (synthetic codes so they never collide with seeded data)
        model = cls.env['pdp.product.model'].create({'code': 'ZZBT'})
        cls.product = cls.env['pdp.product'].create({
            'code': 'ZZBT-X/W', 'model_id': model.id})
        cls.part = cls.env['pdp.part'].create({'code': 'ZST', 'name': 'Z Stud Barrel'})
        cls.part2 = cls.env['pdp.part'].create({'code': 'ZST2', 'name': 'Z Other Part'})
        cls.ppart = cls.env['pdp.product.part'].create({
            'product_id': cls.product.id, 'part_id': cls.part.id, 'quantity': 1})

        # SIS invoice with one matched line and one unmatched (descriptive) line
        cls.doc = cls.env['sis.document'].create({
            'name': 'SI-ZZQ-99001', 'doc_type_code': 'SI'})
        cls.env['sis.document.item'].create({
            'document_id': cls.doc.id, 'sequence': 10,
            'design': 'ZZBT-X/P', 'product_id': cls.product.id, 'qty': 1})
        cls.env['sis.document.item'].create({
            'document_id': cls.doc.id, 'sequence': 20,
            'design': 'CERTIFICATE', 'qty': 1})  # no product → not selected

    def test_get_invoices_lists_si(self):
        names = [d['name'] for d in self.U.get_invoices()]
        self.assertIn('SI-ZZQ-99001', names)

    def test_invoice_designs_pdp_and_selected(self):
        rows = self.U.get_invoice_designs(self.doc.id)
        self.assertEqual(rows[0], {
            'design': 'ZZBT-X/P', 'pdp_design': 'ZZBT-X/W', 'selected': True})
        # descriptive line: no PDP product → not selected
        self.assertEqual(rows[1]['design'], 'CERTIFICATE')
        self.assertFalse(rows[1]['selected'])
        self.assertEqual(rows[1]['pdp_design'], '')

    def test_search_product_parts_filters(self):
        rows = self.U.search_product_parts(model_code='ZZBT', part_id=self.part.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['design'], 'ZZBT-X/W')
        self.assertEqual(rows[0]['part_name'], 'Z Stud Barrel')
        self.assertEqual(rows[0]['part_code'], 'ZST')
        # filtering on a different part returns nothing
        self.assertEqual(self.U.search_product_parts(part_id=self.part2.id), [])

    def test_update_product_parts_reassigns(self):
        n = self.U.update_product_parts([self.ppart.id], self.part2.id)
        self.assertEqual(n, 1)
        self.assertEqual(self.ppart.part_id, self.part2)
