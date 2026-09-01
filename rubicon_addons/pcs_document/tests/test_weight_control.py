from odoo.addons.pcs_document.tests.test_pcs_document import PcsDocumentCase


class TestWeightControl(PcsDocumentCase):
    """The optional weight-control operating mode: per-step gold (grams)
    and stone (carats) weighings, gated by department flags."""

    def setUp(self):
        super().setUp()
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        self.doc = self.env['pcs.document'].browse(doc_id)
        self.barcode = self.doc.barcode_ids.sorted('line_no')[0]
        self.Transaction = self.env['pcs.transaction']

    def _set_mode(self, mode):
        self.Transaction.set_weight_control_mode(mode)

    def test_default_mode_is_off(self):
        self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'pcs.weight_control')]).unlink()
        self.assertEqual(self.Transaction.weight_control_mode(), 'off')

    def test_needs_follow_department_flags(self):
        needs = self.Transaction._weight_needs
        self.assertEqual(needs(self.dept_cst), ['gold'])
        self.assertEqual(needs(self.dept_ast), ['stone'])
        self.assertEqual(needs(self.env.ref('pcs_document.dept_rst')),
                         ['gold', 'stone'])
        self.assertEqual(needs(self.env.ref('pcs_document.dept_shp')), [])

    def test_off_mode_never_blocks(self):
        self._set_mode('off')
        result = self.Transaction.scan(self.barcode.name, self.dept_cst.id)
        self.assertEqual(result['status'], 'issued')

    def test_required_blocks_until_weighed(self):
        self._set_mode('required')
        result = self.Transaction.scan(self.barcode.name, self.dept_cst.id)
        self.assertEqual(result['status'], 'weight_required')
        self.assertEqual(result['action'], 'issue')
        self.assertEqual(result['missing'], ['gold'])
        # nothing was created by the refused scan
        self.assertFalse(self.barcode.transaction_ids)

        result = self.Transaction.scan(
            self.barcode.name, self.dept_cst.id, weight=5.2)
        self.assertEqual(result['status'], 'issued')
        txn = self.Transaction.browse(result['transaction_id'])
        self.assertEqual(txn.issue_weight, 5.2)

        result = self.Transaction.scan(self.barcode.name, self.dept_cst.id)
        self.assertEqual(result['status'], 'weight_required')
        self.assertEqual(result['action'], 'receive')
        result = self.Transaction.scan(
            self.barcode.name, self.dept_cst.id, weight=5.1)
        self.assertEqual(result['status'], 'received')
        self.assertEqual(txn.receive_weight, 5.1)

    def test_required_stone_weights_in_carats(self):
        self._set_mode('required')
        result = self.Transaction.scan(self.barcode.name, self.dept_ast.id)
        self.assertEqual(result['missing'], ['stone'])
        result = self.Transaction.scan(
            self.barcode.name, self.dept_ast.id, stone_weight=2.35,
            note='one stone missing vs PDP')
        self.assertEqual(result['status'], 'issued')
        txn = self.Transaction.browse(result['transaction_id'])
        self.assertEqual(txn.issue_stone_weight, 2.35)
        self.assertEqual(txn.note, 'one stone missing vs PDP')
        result = self.Transaction.scan(
            self.barcode.name, self.dept_ast.id, stone_weight=2.31,
            note='swapped one')
        self.assertEqual(result['status'], 'received')
        self.assertEqual(txn.receive_stone_weight, 2.31)
        self.assertEqual(txn.note, 'one stone missing vs PDP | swapped one')

    def test_optional_records_without_blocking(self):
        self._set_mode('optional')
        result = self.Transaction.scan(self.barcode.name, self.dept_ast.id)
        self.assertEqual(result['status'], 'issued')
        result = self.Transaction.scan(
            self.barcode.name, self.dept_ast.id, stone_weight=2.4)
        self.assertEqual(result['status'], 'received')
        txn = self.Transaction.browse(result['transaction_id'])
        self.assertEqual(txn.receive_stone_weight, 2.4)
