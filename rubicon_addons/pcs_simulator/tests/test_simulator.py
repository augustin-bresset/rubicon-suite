from odoo.tests.common import TransactionCase


class TestSimulator(TransactionCase):
    """The simulator drives pieces through the real scan API."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        def get_or_create(model, domain, vals):
            record = env[model].search(domain, limit=1)
            return record or env[model].create(vals)

        cls.model_plain = env['pdp.product.model'].create({'code': 'ZZSIM1'})
        cls.product_plain = env['pdp.product'].create({
            'code': 'ZZSIM1-PLAIN/Y', 'model_id': cls.model_plain.id,
            'metal': 'Y', 'active': True})

        stone_type = get_or_create(
            'pdp.stone.type', [('code', '=', 'ZZS')],
            {'code': 'ZZS', 'name': 'ZZS'})
        shape = get_or_create(
            'pdp.stone.shape', [('code', '=', 'RD')],
            {'code': 'RD', 'shape': 'RD'})
        size = get_or_create(
            'pdp.stone.size', [('name', '=', '3.0')], {'name': '3.0'})
        stone = get_or_create(
            'pdp.stone', [('code', '=', 'ZZS-RD-3.0')],
            {'code': 'ZZS-RD-3.0', 'type_id': stone_type.id,
             'shape_id': shape.id, 'size_id': size.id})
        composition = env['pdp.product.stone.composition'].create(
            {'code': 'ZZSIM2-COMP'})
        env['pdp.product.stone'].create({
            'composition_id': composition.id, 'stone_id': stone.id,
            'pieces': 4, 'weight': 0.05})
        cls.model_stone = env['pdp.product.model'].create({'code': 'ZZSIM2'})
        cls.product_stone = env['pdp.product'].create({
            'code': 'ZZSIM2-ZZS/Y', 'model_id': cls.model_stone.id,
            'stone_composition_id': composition.id, 'metal': 'Y',
            'active': True})

        cls.sis_doc = env['sis.document'].create({
            'name': 'SO-ZZS-25990',
            'doc_type_code': 'SO',
            'date_created': '2025-05-16',
        })
        env['sis.document.item'].create({
            'document_id': cls.sis_doc.id, 'design': 'ZZSIM1-PLAIN/Y',
            'model_code': 'ZZSIM1', 'purity': '18K', 'metal_code': 'Y',
            'qty': 1.0, 'sequence': 1})
        env['sis.document.item'].create({
            'document_id': cls.sis_doc.id, 'design': 'ZZSIM2-ZZS/Y',
            'model_code': 'ZZSIM2', 'purity': '18K', 'metal_code': 'Y',
            'qty': 1.0, 'sequence': 2})

        cls.Simulator = env['pcs.simulator']

    def setUp(self):
        super().setUp()
        # A live simulation may exist in the dev database; drop its singleton
        # so each test starts from a fresh simulator (rolled back afterwards).
        self.Simulator.search([]).unlink()

    def _setup_sim(self):
        return self.Simulator.setup(references=['SO-ZZS-25990'])

    def test_setup_creates_workers_and_documents(self):
        status = self._setup_sim()
        self.assertEqual(len(status['documents']), 1)
        self.assertEqual(status['documents'][0]['pieces'], 2)
        wax_worker = self.env['pcs.employee'].search(
            [('code', '=', 'SWAX1')])
        self.assertTrue(wax_worker)
        self.assertIn(self.env.ref('pcs_document.dept_wax'),
                      wax_worker.department_ids)

    def test_history_advances_pieces(self):
        self._setup_sim()
        status = self.Simulator.run_history(days=20, tick_hours=8)
        simulator = self.Simulator._get()
        txns = self.env['pcs.transaction'].search(
            [('document_id', 'in', simulator.document_ids.ids)])
        self.assertTrue(txns, "the factory should have produced operations")
        for barcode in simulator.document_ids.mapped('barcode_ids'):
            prod_txns = barcode.transaction_ids.filtered(
                lambda t: t.department_id.track == 'prod').sorted('id')
            self.assertTrue(prod_txns)
            self.assertEqual(prod_txns[0].department_id.code, 'WAX')
        self.assertTrue(status['events'])
        self.assertEqual(status['tick_count'], 60)

    def test_merge_waits_for_stones(self):
        self._setup_sim()
        self.Simulator.run_history(days=40, tick_hours=8)
        simulator = self.Simulator._get()
        barcode = simulator.document_ids.mapped('barcode_ids').filtered(
            lambda b: b.product_id == self.product_stone)
        stone_txns = barcode.transaction_ids.filtered(
            lambda t: t.department_id.track == 'stone')
        self.assertTrue(stone_txns, "the stone track should have started")
        merged = barcode.transaction_ids.filtered(
            lambda t: t.department_id.code == 'MER')
        if merged:
            last_stone = barcode._last_transaction('stone')
            self.assertEqual(last_stone.department_id.code, 'SFN')
            self.assertEqual(last_stone.status, 'fin')

    def test_weights_decrease_in_lossy_departments(self):
        self._setup_sim()
        self.Simulator.run_history(days=40, tick_hours=8)
        simulator = self.Simulator._get()
        lossy = self.env['pcs.transaction'].search([
            ('document_id', 'in', simulator.document_ids.ids),
            ('status', '=', 'fin'),
            ('department_id.loss_pct', '>', 0),
        ])
        for txn in lossy:
            if txn.issue_weight and txn.receive_weight:
                self.assertLess(txn.receive_weight, txn.issue_weight)

    def test_deterministic_with_same_seed(self):
        self._setup_sim()
        self.Simulator.run_history(days=15, tick_hours=8)
        simulator = self.Simulator._get()
        count_first = self.env['pcs.transaction'].search_count(
            [('document_id', 'in', simulator.document_ids.ids)])
        self.Simulator.reset()
        self._setup_sim()
        self.Simulator.run_history(days=15, tick_hours=8)
        simulator = self.Simulator._get()
        count_second = self.env['pcs.transaction'].search_count(
            [('document_id', 'in', simulator.document_ids.ids)])
        self.assertEqual(count_first, count_second)

    def test_get_flow(self):
        self._setup_sim()
        flow = self.Simulator.get_flow()
        self.assertEqual(flow['total_pieces'], 2)
        self.assertFalse(flow['transfers'])
        self.Simulator.tick(8)
        flow = self.Simulator.get_flow()
        # First tick: every piece enters the factory (metal at Wax,
        # stones at Assorting), all transfers come from outside ('').
        self.assertEqual(flow['nodes']['WAX']['wip'], 2)
        targets = {t['to'] for t in flow['transfers']}
        self.assertIn('WAX', targets)
        self.assertIn('AST', targets)
        self.assertTrue(all(t['origin'] == '' for t in flow['transfers']))

    def test_step_operation_stops_at_first_event(self):
        self._setup_sim()
        status = self.Simulator.step_operation()
        self.assertTrue(status['event'])
        simulator = self.Simulator._get()
        txns = self.env['pcs.transaction'].search(
            [('document_id', 'in', simulator.document_ids.ids)])
        self.assertTrue(txns)
        count_before = len(txns)
        status = self.Simulator.step_operation()
        self.assertTrue(status['event'])
        count_after = self.env['pcs.transaction'].search_count([
            ('document_id', 'in', simulator.document_ids.ids)])
        fin_after = self.env['pcs.transaction'].search_count([
            ('document_id', 'in', simulator.document_ids.ids),
            ('status', '=', 'fin')])
        self.assertTrue(count_after > count_before or fin_after > 0)

    def test_advance_hours_splits_into_chunks(self):
        self._setup_sim()
        self.Simulator.advance_hours(24)
        self.assertEqual(self.Simulator._get().tick_count, 3)

    def test_detached_mode_hides_simulation_from_pcs(self):
        self._setup_sim()
        # The dev database may hold other committed simulated documents;
        # unflag them here (rolled back) so the counts below are ours only.
        self.env['pcs.document'].with_context(active_test=False).search([
            ('simulated', '=', True),
            ('id', 'not in', self.Simulator._get().document_ids.ids),
        ]).write({'simulated': False})
        self.Simulator.set_attached(True)
        Service = self.env['pcs.workspace.service']
        names = [d['name'] for d in Service.get_documents()]
        self.assertIn('SO-ZZS-25990', names)

        self.Simulator.set_attached(False)
        self.assertFalse(self.Simulator.is_attached())
        mode = Service.get_sim_mode()
        self.assertFalse(mode['include'])
        self.assertTrue(mode['has_sim'])
        names = [d['name'] for d in Service.get_documents()]
        self.assertNotIn('SO-ZZS-25990', names)

        # The simulation keeps running while detached...
        self.Simulator.tick(8)
        sim_barcodes = self.Simulator._get().document_ids.mapped('barcode_ids')
        rows = Service.get_timeline(barcode_name=sim_barcodes[0].name)
        self.assertTrue(rows['barcodes'][0]['steps'])
        # ...but the dashboard ignores its pieces (2 pieces of qty 1).
        total_detached = Service.get_dashboard('prod')['total_pieces']
        self.Simulator.set_attached(True)
        total_attached = Service.get_dashboard('prod')['total_pieces']
        self.assertEqual(total_attached - total_detached, 2)
        self.Simulator.set_attached(False)

        self.Simulator.set_attached(True)
        names = [d['name'] for d in Service.get_documents()]
        self.assertIn('SO-ZZS-25990', names)

    def test_get_pieces_exposes_barcodes(self):
        self._setup_sim()
        pieces = self.Simulator.get_pieces()
        self.assertEqual(len(pieces), 2)
        piece = pieces[0]
        self.assertEqual(piece['barcode'], 'ZZS25990/1.ZZSIM1')
        self.assertIn('/pcs_document/barcode39', piece['barcode_url'])
        self.assertEqual(piece['prod_position'], 'Not started')
        self.assertFalse(piece['done'])

    def test_scan_piece_uses_sim_clock(self):
        self._setup_sim()
        self.Simulator.tick(8)
        simulator = self.Simulator._get()
        pieces = self.Simulator.get_pieces()
        dept_set = self.env.ref('pcs_document.dept_set')
        result = self.Simulator.scan_piece(
            pieces[0]['barcode'], dept_set.id)
        # The piece is WIP in Wax after the first tick: scanning another
        # prod department is refused, exactly like a physical scan.
        self.assertEqual(result['status'], 'error')
        dept_wax = self.env.ref('pcs_document.dept_wax')
        result = self.Simulator.scan_piece(pieces[0]['barcode'], dept_wax.id)
        self.assertEqual(result['status'], 'received')
        txn = self.env['pcs.transaction'].browse(result['transaction_id'])
        self.assertEqual(txn.receive_date, simulator.sim_time)

    def test_runs_under_required_weight_control(self):
        self.env['pcs.transaction'].set_weight_control_mode('required')
        self._setup_sim()
        self.Simulator.run_history(days=15, tick_hours=8)
        simulator = self.Simulator._get()
        txns = self.env['pcs.transaction'].search(
            [('document_id', 'in', simulator.document_ids.ids)])
        self.assertTrue(txns, "the simulation must pass the weighing gates")
        # the stone-set piece got stone weighings in carats at Assorting
        ast_txns = txns.filtered(
            lambda t: t.department_id.code == 'AST' and t.status == 'fin')
        self.assertTrue(ast_txns)
        self.assertTrue(all(t.receive_stone_weight > 0 for t in ast_txns))
        # gold weighings still happen at metal departments
        cst_txns = txns.filtered(
            lambda t: t.department_id.code == 'CST' and t.status == 'fin')
        for txn in cst_txns:
            self.assertTrue(txn.issue_weight > 0)

    def test_reset_cleans_everything(self):
        self._setup_sim()
        self.Simulator.run_history(days=10, tick_hours=8)
        simulator = self.Simulator._get()
        doc_ids = simulator.document_ids.ids
        self.Simulator.reset()
        self.assertFalse(self.env['pcs.document'].with_context(
            active_test=False).search([('id', 'in', doc_ids)]))
        self.assertFalse(self.env['pcs.transaction'].search(
            [('document_id', 'in', doc_ids)]))
        self.assertEqual(self.Simulator._get().tick_count, 0)
