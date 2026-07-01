from odoo.tests.common import TransactionCase


class TestSisItemProductLink(TransactionCase):
    """sis.document.item.product_id is derived from the design code (Lot 2)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.model = cls.env['pdp.product.model'].create({'code': 'ZLNKMOD'})
        cls.product = cls.env['pdp.product'].create({
            'code': 'ZLNKMOD-RU/W', 'model_id': cls.model.id, 'active': True, 'metal': 'W',
        })
        cls.doc = cls.env['sis.document'].create({
            'name': 'SO-ZLK-90001', 'doc_type_code': 'SO',
        })

    def _item(self, **vals):
        vals.setdefault('document_id', self.doc.id)
        vals.setdefault('qty', 1)
        return self.env['sis.document.item'].create(vals)

    def test_create_links_product_by_design(self):
        item = self._item(design='ZLNKMOD-RU/W')
        self.assertEqual(item.product_id, self.product)

    def test_create_unmatched_design_leaves_null(self):
        item = self._item(design='NOSUCH-CODE/W')
        self.assertFalse(item.product_id)

    def test_create_respects_explicit_product_id(self):
        # An explicit product_id wins even if design points elsewhere.
        item = self._item(design='NOSUCH-CODE/W', product_id=self.product.id)
        self.assertEqual(item.product_id, self.product)

    def test_write_design_relinks(self):
        item = self._item(design='NOSUCH/W')
        self.assertFalse(item.product_id)
        item.write({'design': 'ZLNKMOD-RU/W'})
        self.assertEqual(item.product_id, self.product)

    def test_write_design_to_unmatched_clears_link(self):
        item = self._item(design='ZLNKMOD-RU/W')
        self.assertEqual(item.product_id, self.product)
        item.write({'design': 'NOSUCH/W'})
        self.assertFalse(item.product_id)

    def test_links_archived_product(self):
        archived = self.env['pdp.product'].create({
            'code': 'ZLNKMOD-DTS/W', 'model_id': self.model.id,
            'active': False, 'metal': 'W',
        })
        item = self._item(design='ZLNKMOD-DTS/W')
        self.assertEqual(item.product_id, archived)

    def test_links_by_legacy_code_when_renamed(self):
        # A product renamed to a structured code keeps its old code in
        # legacy_code; a design snapshot holding that old code still links.
        renamed = self.env['pdp.product'].create({
            'code': 'ZLNKMOD-DTS/W', 'legacy_code': 'OLDCODE-42/W',
            'model_id': self.model.id, 'active': True, 'metal': 'W',
        })
        item = self._item(design='OLDCODE-42/W')
        self.assertEqual(item.product_id, renamed)

    def test_current_code_wins_over_legacy_code(self):
        # When a design matches one product's current code and another's legacy
        # code, the current-code match takes precedence.
        current = self.env['pdp.product'].create({
            'code': 'SHARED-CODE/W', 'model_id': self.model.id,
            'active': True, 'metal': 'W',
        })
        self.env['pdp.product'].create({
            'code': 'ZLNKMOD-XX/W', 'legacy_code': 'SHARED-CODE/W',
            'model_id': self.model.id, 'active': True, 'metal': 'W',
        })
        item = self._item(design='SHARED-CODE/W')
        self.assertEqual(item.product_id, current)

    def test_backfill_links_unlinked_items(self):
        item = self._item(design='ZLNKMOD-RU/W')
        # Simulate legacy data where the FK was never populated.
        self.env.cr.execute(
            "UPDATE sis_document_item SET product_id = NULL WHERE id = %s", (item.id,))
        item.invalidate_recordset(['product_id'])
        self.assertFalse(item.product_id)

        result = self.env['sis.document.item']._backfill_product_links()

        item.invalidate_recordset(['product_id'])
        self.assertEqual(item.product_id, self.product)
        self.assertGreaterEqual(result['linked'], 1)
