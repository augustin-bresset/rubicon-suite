from odoo.addons.pcs_document.tests.test_pcs_document import PcsDocumentCase


class TestWorkspaceService(PcsDocumentCase):
    """The workspace RPC layer feeds every PCS screen."""

    def setUp(self):
        super().setUp()
        self.Service = self.env['pcs.workspace.service']
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        self.doc = self.env['pcs.document'].browse(doc_id)
        self.barcode_a, self.barcode_b = self.doc.barcode_ids.sorted('line_no')
        self.Transaction = self.env['pcs.transaction']

    def test_sales_docs(self):
        rows = self.Service.get_sales_docs()
        names = [r['name'] for r in rows]
        self.assertIn('SO-ZZP-25990', names)
        items = self.Service.get_sales_doc_items(self.sis_doc.id)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['design'], 'ZZPC1-CT2A+GA/Y')

    def test_documents_and_barcodes(self):
        rows = self.Service.get_documents()
        self.assertTrue(any(r['name'] == 'SO-ZZP-25990' for r in rows))
        barcodes = self.Service.get_barcodes(self.doc.id)
        self.assertEqual(len(barcodes), 2)
        self.Service.update_barcode(
            barcodes[0]['id'], {'tag': 'WITH SAPF+TT', 'priority': True,
                                'design': 'ignored'})
        self.barcode_a.invalidate_recordset()
        self.assertEqual(self.barcode_a.tag, 'WITH SAPF+TT')
        self.assertTrue(self.barcode_a.priority)
        self.assertEqual(self.barcode_a.design, 'ZZPC1-CT2A+GA/Y')

    def test_document_active_toggle(self):
        self.Service.set_document_active(self.doc.id, False)
        self.assertFalse(self.doc.active)
        rows = self.Service.get_documents(active_only=True)
        self.assertFalse(any(r['name'] == 'SO-ZZP-25990' for r in rows))
        rows = self.Service.get_documents(active_only=False)
        self.assertTrue(any(r['name'] == 'SO-ZZP-25990' for r in rows))

    def test_dashboard_counts(self):
        # The dashboard aggregates every active document; hide the ones a
        # live dev database may contain (rolled back after the test).
        self.env['pcs.document'].search(
            [('id', '!=', self.doc.id)]).write({'active': False})
        self.Transaction.scan(self.barcode_a.name, self.dept_wax.id)
        self.Transaction.scan(self.barcode_b.name, self.dept_wax.id)
        self.Transaction.scan(self.barcode_b.name, self.dept_wax.id)  # receive
        result = self.Service.get_dashboard('prod')
        cells = {c['code']: c for c in result['cells']}
        self.assertEqual(cells['WAX']['work'], 1)
        self.assertEqual(cells['WAX']['finish'], 1)
        # once moved to casting, the wax 'finish' slot frees up
        self.Transaction.scan(self.barcode_b.name, self.dept_cst.id)
        result = self.Service.get_dashboard('prod')
        cells = {c['code']: c for c in result['cells']}
        self.assertEqual(cells['WAX']['finish'], 0)
        self.assertEqual(cells['CST']['work'], 1)

    def test_dashboard_barcode_filter(self):
        self.Transaction.scan(self.barcode_a.name, self.dept_wax.id)
        result = self.Service.get_dashboard('prod', barcode=self.barcode_a.name)
        self.assertEqual(result['total_pieces'], 1)
        cells = {c['code']: c for c in result['cells']}
        self.assertEqual(cells['WAX']['work'], 1)

    def test_pbarcodes(self):
        self.Transaction.scan(self.barcode_a.name, self.dept_wax.id)
        rows = self.Service.get_pbarcodes(self.doc.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['pbarcode'], 'P01-' + self.barcode_a.name)
        self.assertEqual(rows[0]['dept'], 'Wax')

    def test_priorities(self):
        self.Service.set_priority(self.doc.id, 3)
        rows = self.Service.get_priorities()
        row = next(r for r in rows if r['name'] == 'SO-ZZP-25990')
        self.assertEqual(row['priority_no'], 3)

    def test_scan_config(self):
        config = self.Service.get_scan_config()
        codes = [d['code'] for d in config['departments']]
        self.assertIn('WAX', codes)
        self.assertIn('AST', codes)
        self.assertIn(config['weight_control'], ('off', 'optional', 'required'))
        by_code = {d['code']: d for d in config['departments']}
        self.assertEqual(by_code['CST']['needs'], ['gold'])
        self.assertEqual(by_code['AST']['needs'], ['stone'])

    def test_pcs_settings_roundtrip(self):
        self.Service.set_pcs_settings({'weight_control': 'required'})
        self.assertEqual(self.Service.get_pcs_settings(),
                         {'weight_control': 'required'})
        with self.assertRaises(ValueError):
            self.Service.set_pcs_settings({'weight_control': 'bogus'})

    def test_ssp_consumption_worker_month(self):
        from dateutil.relativedelta import relativedelta
        from odoo import fields as odoo_fields
        today = odoo_fields.Date.context_today(self.Service)
        start = today.replace(day=18)
        if today.day < 18:
            start -= relativedelta(months=1)
        ssp = self.env['pcs.ssp'].search([('code', '=', 'WIR')], limit=1)
        self.assertTrue(ssp, "gold wire must be seeded")
        emp = self.env['pcs.employee'].create(
            {'code': 'ZZF1', 'name': 'ZZ Filer'})
        inside = self.env['pcs.ssp.transaction'].create({
            'ssp_id': ssp.id, 'employee_id': emp.id, 'purity': '18K',
            'issue_weight': 20.0, 'receive_weight': 6.5, 'date': start})
        self.env['pcs.ssp.transaction'].create({
            'ssp_id': ssp.id, 'employee_id': emp.id, 'purity': '18K',
            'issue_weight': 99.0, 'date': start - relativedelta(days=1)})
        report = self.Service.report_ssp_consumption(0)
        row = next(r for r in report['rows'] if r['worker'] == 'ZZ Filer')
        self.assertEqual(row['issued'], 20.0)
        self.assertEqual(row['consumed'], 13.5)
        # the out-of-window issue shows up in the previous worker month
        report = self.Service.report_ssp_consumption(-1)
        row = next(r for r in report['rows'] if r['worker'] == 'ZZ Filer')
        self.assertEqual(row['issued'], 99.0)
        self.assertTrue(inside.exists())

    def test_report_multi(self):
        self.Transaction.scan(self.barcode_a.name, self.dept_wax.id, weight=5.0)
        self.Transaction.scan(self.barcode_a.name, self.dept_wax.id, weight=4.8)
        result = self.Service.report_multi(self.dept_wax.id)
        # The report covers the whole department: keep only our piece
        # (the dev database may hold other transactions).
        cutting = [r for r in result['cutting']
                   if r['ref'] == self.barcode_a.name]
        self.assertEqual(len(cutting), 1)
        self.assertEqual(cutting[0]['i_weight'], 5.0)
        self.assertEqual(cutting[0]['r_weight'], 4.8)
        filling = next(r for r in result['filling']
                       if r['order'] == 'SO-ZZP-25990')
        # 18K -> 75% fine gold
        self.assertEqual(filling['given_wt_100'], 3.75)
        self.assertEqual(filling['diff_wt'], 0.2)

    def test_report_doc_items_dept_cost(self):
        self.Transaction.scan(self.barcode_a.name, self.dept_cst.id)
        rows = self.Service.report_doc_items_dept_cost()
        row = next(r for r in rows if r['ref'] == self.barcode_a.name)
        self.assertEqual(row['in_casting'], 1)
        self.assertEqual(row['casting'], 0)
        self.assertEqual(row['stone_detail'], 'CT2A+GA')
        self.assertEqual(row['gold'], 'Y')

    def test_report_doc_items_finish(self):
        dept_fin = self.env.ref('pcs_document.dept_fin')
        self.Transaction.scan(self.barcode_a.name, dept_fin.id)
        self.Transaction.scan(self.barcode_a.name, dept_fin.id)
        rows = self.Service.report_doc_items_finish()
        self.assertTrue(
            any(r['barcode'] == self.barcode_a.name for r in rows))

    def test_report_priorities(self):
        # assorted, never casted -> shows up in 'assorted' mode
        self.Transaction.scan(self.barcode_a.name, self.dept_ast.id)
        self.Transaction.scan(self.barcode_a.name, self.dept_ast.id)
        result = self.Service.report_priorities('assorted')
        self.assertTrue(
            any(r['barcode'] == self.barcode_a.name for r in result['bottom']))
        row = next(r for r in result['bottom']
                   if r['barcode'] == self.barcode_a.name)
        self.assertTrue(row['no_cast'])
        self.assertFalse(row['no_assort'])

    def test_report_sis_not_in_pcs(self):
        other = self.env['sis.document'].create({
            'name': 'SO-ZZP-25995',
            'doc_type_code': 'SO',
            'date_created': '2025-05-16',
        })
        self.env['sis.document.item'].create({
            'document_id': other.id, 'design': 'ZZPC1-CT2A+GA/Y', 'qty': 1.0})
        rows = self.Service.report_sis_not_in_pcs()
        names = [r['doc_name'] for r in rows]
        self.assertIn('SO-ZZP-25995', names)
        self.assertNotIn('SO-ZZP-25990', names)

    def test_report_wax_pdp_weight(self):
        rows = self.Service.report_wax_pdp_weight()
        names = [r['barcode'] for r in rows]
        # both pieces have no production transaction yet
        self.assertIn(self.barcode_a.name, names)
        self.assertIn(self.barcode_b.name, names)

    def test_timeline(self):
        self.Transaction.scan(self.barcode_a.name, self.dept_wax.id, weight=5.0)
        self.Transaction.scan(self.barcode_a.name, self.dept_wax.id, weight=4.9)
        self.Transaction.scan(self.barcode_a.name, self.dept_ast.id,
                              stone_weight=2.2)
        result = self.Service.get_timeline(document_id=self.doc.id)
        line = next(l for l in result['barcodes']
                    if l['barcode'] == self.barcode_a.name)
        self.assertEqual(len(line['steps']), 2)
        wax_step, ast_step = line['steps']
        self.assertEqual(wax_step['dept_code'], 'WAX')
        self.assertEqual(wax_step['status'], 'fin')
        self.assertEqual(wax_step['track'], 'prod')
        self.assertEqual(wax_step['receive_weight'], 4.9)
        self.assertEqual(ast_step['dept_code'], 'AST')
        self.assertEqual(ast_step['status'], 'wip')
        self.assertEqual(ast_step['track'], 'stone')
        self.assertEqual(ast_step['issue_stone_weight'], 2.2)

    def test_report_dashboard_summary(self):
        self.Transaction.scan(self.barcode_a.name, self.dept_cst.id)
        rows = self.Service.report_dashboard_summary()
        row = next(r for r in rows if r['sales_order'] == 'SO-ZZP-25990')
        self.assertEqual(row['casting'], 1)
        self.assertEqual(row['total'], 2)
