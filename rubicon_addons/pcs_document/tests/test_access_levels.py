"""Production Operator access level (audit, meta/audit.pdf section 2.3).

Quality controllers and lapidary supervisors record scans, weighings and
clearances on the floor, but must not edit master data (products, prices)
nor create or delete production documents.
"""
from odoo.exceptions import AccessError
from odoo.tools import mute_logger

from .test_pcs_document import PcsDocumentCase


class TestProductionOperator(PcsDocumentCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operator = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Floor operator', 'login': 'floor_operator',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('rubicon_env.group_rubicon_production').id,
            ])],
        })
        doc_id = cls.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        cls.doc = cls.env['pcs.document'].browse(doc_id)
        cls.barcode = cls.doc.barcode_ids.sorted('line_no')[0]

    def test_operator_scans_and_updates_the_floor(self):
        Transaction = self.env['pcs.transaction'].with_user(self.operator)
        result = Transaction.scan(self.barcode.name, self.dept_wax.id)
        self.assertEqual(result['status'], 'issued')
        txn = Transaction.browse(result['transaction_id'])
        self.assertEqual(txn.status, 'wip')
        self.barcode.with_user(self.operator).write({'tag': 'WITH SAPF+TT'})
        self.assertEqual(self.barcode.tag, 'WITH SAPF+TT')

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.addons.base.models.ir_rule')
    def test_operator_touches_no_master_data(self):
        with self.assertRaises(AccessError):
            self.product_a.with_user(self.operator).write({'metal': 'P'})
        with self.assertRaises(AccessError):
            self.env['pdp.product.category'].with_user(self.operator).create(
                {'code': 'ZFL', 'name': 'floor', 'waste': 0.0})
        with self.assertRaises(AccessError):
            self.env['pcs.document'].with_user(self.operator).create(
                {'name': 'SO-ZZP-25999'})
        with self.assertRaises(AccessError):
            self.doc.with_user(self.operator).unlink()

    def test_roles_imply_production(self):
        ref = self.env.ref
        production = ref('rubicon_env.group_rubicon_production')
        self.assertIn(production, ref('rubicon_env.group_rubicon_quality_controller').implied_ids)
        self.assertIn(production, ref('rubicon_env.group_rubicon_lapidary_supervisor').implied_ids)
        self.assertIn(ref('rubicon_env.group_rubicon_user'), production.implied_ids)
