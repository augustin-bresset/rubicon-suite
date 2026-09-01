from odoo.tests.common import TransactionCase


class TestStockCard(TransactionCase):
    """The stock card data getter reproduces the legacy card content.

    Fixture codes use a ZZ prefix to stay clear of real records when the
    suite runs on a development database.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        thb = env['res.currency'].with_context(active_test=False).search(
            [('name', '=', 'THB')], limit=1)
        thb.active = True

        cls.model = env['pdp.product.model'].create({'code': 'ZZPC9'})
        purity = env['pdp.metal.purity'].search([('code', '=', '18K')], limit=1)
        if not purity:
            purity = env['pdp.metal.purity'].create({'code': '18K'})
        env['pdp.product.model.metal'].create({
            'model_id': cls.model.id, 'metal_version': 'P',
            'purity_id': purity.id, 'weight': 4.9})
        labor_fil = env['pdp.labor.type'].search(
            [('code', '=', 'FIL')], limit=1)
        if not labor_fil:
            labor_fil = env['pdp.labor.type'].create(
                {'code': 'FIL', 'name': 'Filing'})
        env['pdp.labor.cost.model'].create({
            'model_id': cls.model.id, 'metal': 'P', 'labor_id': labor_fil.id,
            'cost': 180.0, 'currency_id': thb.id})

        def get_or_create(model, domain, vals):
            record = env[model].search(domain, limit=1)
            return record or env[model].create(vals)

        stone_type = get_or_create(
            'pdp.stone.type', [('code', '=', 'ZZT')],
            {'code': 'ZZT', 'name': 'ZZT'})
        shape = get_or_create(
            'pdp.stone.shape', [('code', '=', 'RD')],
            {'code': 'RD', 'shape': 'RD'})
        shade = get_or_create(
            'pdp.stone.shade', [('code', '=', 'GR')],
            {'code': 'GR', 'shade': 'GR'})
        size = get_or_create(
            'pdp.stone.size', [('name', '=', '2.2')], {'name': '2.2'})
        cls.stone = env['pdp.stone'].create({
            'code': 'ZZTGR-RD-2.2', 'type_id': stone_type.id,
            'shape_id': shape.id, 'shade_id': shade.id, 'size_id': size.id})
        composition = env['pdp.product.stone.composition'].create(
            {'code': 'ZZPC9-COMP'})
        env['pdp.product.stone'].create({
            'composition_id': composition.id, 'stone_id': cls.stone.id,
            'pieces': 1, 'weight': 0.0132, 'setting': 12.0})
        cls.product = env['pdp.product'].create({
            'code': 'ZZPC9-GA+RH/P', 'model_id': cls.model.id,
            'stone_composition_id': composition.id, 'metal': 'P',
            'active': True})

        cls.sis_doc = env['sis.document'].create({
            'name': 'SO-ZZP-25991',
            'doc_type_code': 'SO',
            'date_created': '2025-05-16',
            'date_due': '2025-06-13',
            'customer_po': '8114',
            'employee': 'PALA',
            'legacy_id': 13335,
        })
        cls.item = env['sis.document.item'].create({
            'document_id': cls.sis_doc.id,
            'design': 'ZZPC9-GA+RH/P',
            'model_code': 'ZZPC9',
            'purity': '18K',
            'metal_code': 'P',
            'qty': 1.0,
            'sequence': 6,
        })
        doc_id = env['pcs.document'].create_from_reference('SO-ZZP-25991')
        cls.doc = env['pcs.document'].browse(doc_id)
        cls.barcode = cls.doc.barcode_ids[0]

    def test_card_data(self):
        card = self.barcode.get_stock_card_data()
        self.assertEqual(card['barcode'], 'ZZP25991/1.ZZPC9')
        self.assertEqual(card['model_code'], 'ZZPC9')
        self.assertEqual(card['design'], 'ZZPC9-GA+RH/P')
        self.assertEqual(card['so_name'], 'SO-ZZP-25991')
        self.assertEqual(card['order_no'], 13335)
        self.assertEqual(card['customer_po'], '8114')
        self.assertEqual(card['employee'], 'PALA')
        self.assertEqual(card['header_center'], '#8114 PALA 16/05/2025')
        self.assertEqual(card['corner_ref'], 'ZZP')
        self.assertEqual(card['qty'], 1)
        self.assertEqual(card['gold_weight'], 4.9)
        # 180 THB filing at 1.4 THB/min -> 128.57 minutes (P720 reference)
        self.assertEqual(card['filing_min'], 128.57)
        # 12 THB setting at 1.45 THB/min -> 8.28 minutes
        self.assertEqual(card['setting_min'], 8.28)
        self.assertEqual(card['metal_letter'], 'P')
        self.assertEqual(card['purity'], '18K')
        self.assertNotEqual(card['stamp_color'], '#ffffff')
        self.assertIn('ZZP25991%2F1.ZZPC9', card['barcode_url'])

    def test_card_stones(self):
        card = self.barcode.get_stock_card_data()
        self.assertEqual(len(card['stones']), 1)
        stone = card['stones'][0]
        self.assertEqual(stone['code'], 'ZZTGR-RD-2.2')
        self.assertEqual(stone['pieces'], 1)
        self.assertEqual(stone['recut_shape'], 'RD')
        self.assertEqual(stone['recut_size'], '2.2')

    def test_report_renders_html(self):
        html = self.env['ir.actions.report']._render_qweb_html(
            'pcs_document.report_stock_card', self.barcode.ids)[0]
        self.assertIn(b'ZZP25991/1.ZZPC9', html)
        self.assertIn(b'ZZTGR-RD-2.2', html)
        self.assertIn(b'STAMP', html)

    def test_print_action_from_document(self):
        action = self.doc.action_print_stock_cards()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(
            action['report_name'], 'pcs_document.report_stock_card')
