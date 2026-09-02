from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestModelDeletionGuard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.model = self.env['pdp.product.model'].create({'code': 'ZZGRD'})
        self.product = self.env['pdp.product'].create({
            'code': 'ZZGRD-GA/Y', 'model_id': self.model.id, 'metal': 'Y'})

    def test_model_with_products_cannot_be_deleted(self):
        with self.assertRaises(UserError):
            self.model.unlink()
        self.assertTrue(self.model.exists())

    def test_force_delete_context_bypasses_the_guard(self):
        self.model.with_context(rubicon_force_delete=True).unlink()
        self.assertFalse(self.model.exists())
        # model_id has no ondelete clause, so the product survives, orphaned —
        # exactly what the guard protects interactive users from.
        self.assertTrue(self.product.exists())
        self.assertFalse(self.product.model_id)

    def test_empty_model_deletes_normally(self):
        self.product.unlink()
        self.model.unlink()
        self.assertFalse(self.model.exists())
