from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class PcsDocumentCase(TransactionCase):
    """Shared fixtures: a sales order with two items linked to PDP products.

    Codes use a ZZ prefix so the tests never collide with real records of a
    development database (same convention as the sis_document tests).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.model_a = env['pdp.product.model'].create({'code': 'ZZPC1'})
        cls.model_b = env['pdp.product.model'].create({'code': 'ZZPC2'})
        cls.product_a = env['pdp.product'].create({
            'code': 'ZZPC1-CT2A+GA/Y', 'model_id': cls.model_a.id,
            'metal': 'Y', 'active': True})
        cls.product_b = env['pdp.product'].create({
            'code': 'ZZPC2-GA+RH/P', 'model_id': cls.model_b.id,
            'metal': 'P', 'active': True})
        cls.sis_doc = env['sis.document'].create({
            'name': 'SO-ZZP-25990',
            'doc_type_code': 'SO',
            'date_created': '2025-05-16',
            'date_due': '2025-06-13',
        })
        cls.item_a = env['sis.document.item'].create({
            'document_id': cls.sis_doc.id,
            'design': 'ZZPC1-CT2A+GA/Y',
            'model_code': 'ZZPC1',
            'purity': '18K',
            'metal_code': 'Y',
            'qty': 1.0,
            'size_remarks': '53',
            'sequence': 1,
        })
        cls.item_b = env['sis.document.item'].create({
            'document_id': cls.sis_doc.id,
            'design': 'ZZPC2-GA+RH/P',
            'model_code': 'ZZPC2',
            'purity': '18K',
            'metal_code': 'P',
            'qty': 1.0,
            'sequence': 2,
        })
        cls.dept_wax = env.ref('pcs_document.dept_wax')
        cls.dept_cst = env.ref('pcs_document.dept_cst')
        cls.dept_ast = env.ref('pcs_document.dept_ast')


class TestPcsDocument(PcsDocumentCase):

    def test_create_from_reference_generates_barcodes(self):
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        doc = self.env['pcs.document'].browse(doc_id)
        self.assertEqual(doc.name, 'SO-ZZP-25990')
        self.assertEqual(len(doc.barcode_ids), 2)
        names = doc.barcode_ids.sorted('line_no').mapped('name')
        self.assertEqual(names, ['ZZP25990/1.ZZPC1', 'ZZP25990/2.ZZPC2'])
        first = doc.barcode_ids.sorted('line_no')[0]
        self.assertEqual(first.design, 'ZZPC1-CT2A+GA/Y')
        self.assertEqual(first.purity, '18K')
        self.assertEqual(first.size, '53')
        self.assertEqual(first.product_id, self.product_a)

    def test_create_from_unknown_reference_raises(self):
        with self.assertRaises(UserError):
            self.env['pcs.document'].create_from_reference('SO-ZZX-99999')

    def test_create_twice_raises(self):
        self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        with self.assertRaises(UserError):
            self.env['pcs.document'].create_from_reference('SO-ZZP-25990')

    def test_update_pdp_adds_new_items(self):
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        doc = self.env['pcs.document'].browse(doc_id)
        self.env['sis.document.item'].create({
            'document_id': self.sis_doc.id,
            'design': 'ZZPC1-CT2A+GA/Y',
            'model_code': 'ZZPC1',
            'qty': 2.0,
            'sequence': 3,
        })
        doc.action_update_pdp()
        self.assertEqual(len(doc.barcode_ids), 3)
        self.assertEqual(
            doc.barcode_ids.sorted('line_no')[-1].name, 'ZZP25990/3.ZZPC1')
        self.assertEqual(doc.total_qty, 4.0)


class TestSisStockCards(PcsDocumentCase):
    """SIS-side stock cards (legacy SIS Report): printable before and
    after the order is registered in production, same barcodes."""

    def test_cards_without_pcs_registration(self):
        cards = self.sis_doc._get_stock_card_datas()
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0]['barcode'], 'ZZP25990/1.ZZPC1')
        self.assertEqual(cards[1]['barcode'], 'ZZP25990/2.ZZPC2')
        self.assertEqual(cards[0]['design'], 'ZZPC1-CT2A+GA/Y')
        html = self.env['ir.actions.report']._render_qweb_html(
            'pcs_document.report_stock_card_sis', self.sis_doc.ids)[0]
        self.assertIn(b'ZZP25990/1.ZZPC1', html)
        self.assertIn(b'ZZP25990/2.ZZPC2', html)
        self.assertIn(b'Sub Part', html)

    def test_cards_follow_pcs_barcodes_once_registered(self):
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        doc = self.env['pcs.document'].browse(doc_id)
        doc.barcode_ids.sorted('line_no')[0].tag = 'WITH SAPF+TT'
        cards = self.sis_doc._get_stock_card_datas()
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0]['tag'], 'WITH SAPF+TT')

    def test_print_action(self):
        action = self.sis_doc.action_print_stock_cards()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(
            action['report_name'], 'pcs_document.report_stock_card_sis')

    def test_barcode_symbology(self):
        cards = self.sis_doc._get_stock_card_datas()
        # Code 39 without checksum for plain references (legacy symbology)
        self.assertIn('/pcs_document/barcode39', cards[0]['barcode_url'])
        # The controller's rendering call accepts checksum=0
        from reportlab.graphics.barcode import createBarcodeDrawing
        png = createBarcodeDrawing(
            'Standard39', value='ZZP25990/1.ZZPC1', format='png',
            width=600, height=90, checksum=0, quiet=True,
            humanReadable=False).asString('png')
        self.assertTrue(png.startswith(b'\x89PNG'))

    def test_barcode_symbology_fallback_code128(self):
        # '&' cannot be encoded in plain Code 39: fall back to Code 128
        # instead of letting reportlab silently drop the character.
        sis_doc = self.env['sis.document'].create({
            'name': 'SO-Z&Q-25990',
            'doc_type_code': 'SO',
            'date_created': '2025-05-16',
        })
        self.env['sis.document.item'].create({
            'document_id': sis_doc.id,
            'design': 'ZZPC1-CT2A+GA/Y',
            'model_code': 'ZZPC1',
            'qty': 1.0,
        })
        cards = sis_doc._get_stock_card_datas()
        self.assertEqual(cards[0]['barcode'], 'Z&Q25990/1.ZZPC1')
        self.assertIn('barcode_type=Code128', cards[0]['barcode_url'])

    def test_sub_part_falls_back_to_model(self):
        cards = self.sis_doc._get_stock_card_datas()
        self.assertEqual(cards[0]['parts'],
                         [{'code': 'ZZPC1', 'name': '', 'quantity': 1}])

    def test_labor_minute_rates_roundtrip(self):
        SisDocument = self.env['sis.document']
        SisDocument.set_labor_minute_rates(1.5, 1.6)
        self.assertEqual(SisDocument.get_labor_minute_rates(),
                         {'filling': 1.5, 'setting': 1.6})
        # Legacy defaults apply when the parameters are absent
        self.env['ir.config_parameter'].sudo().search(
            [('key', 'like', 'pcs.labor_minute_rate%')]).unlink()
        self.assertEqual(SisDocument.get_labor_minute_rates(),
                         {'filling': 1.4, 'setting': 1.45})

    def test_year_and_ref_selectors(self):
        years = self.env['sis.document'].get_stock_card_years()
        self.assertIn(2025, years)
        orders = self.env['sis.document'].get_stock_card_orders(2025)
        names = [o['name'] for o in orders]
        self.assertIn('SO-ZZP-25990', names)


class TestPriorityList(PcsDocumentCase):

    def test_priority_list_report(self):
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        doc = self.env['pcs.document'].browse(doc_id)
        doc.priority_no = 5
        action = self.env['pcs.document'].action_print_priority_list()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(
            action['report_name'], 'pcs_document.report_priority_list')
        html = self.env['ir.actions.report']._render_qweb_html(
            'pcs_document.report_priority_list', doc.ids)[0]
        self.assertIn(b'Priority List', html)
        self.assertIn(b'SO-ZZP-25990', html)
        self.assertIn(b'16/05/2025', html)


class TestPcsScan(PcsDocumentCase):

    def setUp(self):
        super().setUp()
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        self.doc = self.env['pcs.document'].browse(doc_id)
        self.barcode = self.doc.barcode_ids.sorted('line_no')[0]
        self.Transaction = self.env['pcs.transaction']

    def test_scan_issue_then_receive(self):
        result = self.Transaction.scan(self.barcode.name, self.dept_wax.id)
        self.assertEqual(result['status'], 'issued')
        txn = self.Transaction.browse(result['transaction_id'])
        self.assertEqual(txn.status, 'wip')
        self.assertEqual(txn.department_id, self.dept_wax)

        result = self.Transaction.scan(self.barcode.name, self.dept_wax.id,
                                       weight=4.31)
        self.assertEqual(result['status'], 'received')
        self.assertEqual(txn.status, 'fin')
        self.assertEqual(txn.receive_weight, 4.31)

    def test_scan_blocked_by_open_wip_on_same_track(self):
        self.Transaction.scan(self.barcode.name, self.dept_wax.id)
        result = self.Transaction.scan(self.barcode.name, self.dept_cst.id)
        self.assertEqual(result['status'], 'error')
        self.assertIn('Wax', result['message'])

    def test_stone_track_is_independent(self):
        self.Transaction.scan(self.barcode.name, self.dept_wax.id)
        result = self.Transaction.scan(self.barcode.name, self.dept_ast.id)
        self.assertEqual(result['status'], 'issued')
        dept, status = self.barcode.track_status('stone')
        self.assertEqual(dept, self.dept_ast)
        self.assertEqual(status, 'WIP')
        dept, status = self.barcode.track_status('prod')
        self.assertEqual(dept, self.dept_wax)
        self.assertEqual(status, 'WIP')

    def test_scan_accepts_pbarcode_prefix(self):
        result = self.Transaction.scan('P01-' + self.barcode.name,
                                       self.dept_wax.id)
        self.assertEqual(result['status'], 'issued')

    def test_scan_unknown_barcode(self):
        result = self.Transaction.scan('ZZNOPE/1.X', self.dept_wax.id)
        self.assertEqual(result['status'], 'error')

    def test_pbarcode_format(self):
        result = self.Transaction.scan(self.barcode.name, self.dept_wax.id)
        txn = self.Transaction.browse(result['transaction_id'])
        self.assertEqual(txn.pbarcode, 'P01-ZZP25990/1.ZZPC1')
        result = self.Transaction.scan(self.barcode.name, self.dept_ast.id)
        txn = self.Transaction.browse(result['transaction_id'])
        self.assertEqual(txn.pbarcode, 'S01-ZZP25990/1.ZZPC1')

    def test_departments_seeded(self):
        self.assertEqual(self.dept_wax.track, 'prod')
        self.assertEqual(self.dept_ast.track, 'stone')
        merged = self.env.ref('pcs_document.dept_mer')
        self.assertEqual(merged.track, 'prod')
        # Workshop divisions: Stone, Metal, Assembly, Quality Controller
        self.assertEqual(self.dept_wax.division_id.code, 'MET')
        self.assertEqual(self.dept_ast.division_id.code, 'STO')
        self.assertEqual(self.env.ref('pcs_document.dept_set').division_id.code,
                         'ASB')
        for code in range(1, 9):
            dept = self.env.ref('pcs_document.dept_qc%d' % code)
            self.assertEqual(dept.division_id.code, 'QC', dept.name)
            self.assertTrue(dept.is_qc, dept.name)
        repair_gold = self.env.ref('pcs_document.dept_qc11')
        self.assertEqual(repair_gold.division_id.code, 'MET',
                         "Repair Gold belongs to the Metal Department")
        self.assertFalse(repair_gold.is_qc)
        self.assertFalse(self.dept_wax.is_qc)
        # Flow-less states belong to no division
        self.assertFalse(self.env.ref('pcs_document.dept_cnl').division_id)
