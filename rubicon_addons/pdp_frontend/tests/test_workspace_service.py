from odoo.tests.common import TransactionCase


class TestWorkspaceService(TransactionCase):
    """Atomic-save service used by the PDP OWL workspace."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.svc = cls.env['pdp.workspace.service']

        cls.model = cls.env['pdp.product.model'].create({'code': 'WS-MOD'})
        cls.product = cls.env['pdp.product'].create({
            'code': 'WS-PROD', 'model_id': cls.model.id, 'active': True,
        })
        cls.currency = cls.env['res.currency'].create({'name': 'WC', 'symbol': 'WC'})

        cls.part_type = cls.env['pdp.part'].create({'code': 'WPART', 'name': 'WS Part'})
        cls.addon_type = cls.env['pdp.addon.type'].create({'code': 'WADD', 'name': 'WS Addon'})
        cls.labor_type = cls.env['pdp.labor.type'].create({'code': 'WLAB', 'name': 'WS Labor'})
        cls.metal = cls.env['pdp.metal'].create({'code': 'WMET', 'name': 'WS Metal'})
        cls.purity = cls.env['pdp.metal.purity'].create({'code': 'W18', 'percent': 75.0})

        cls.stone_type = cls.env['pdp.stone.type'].create({'code': 'WSTY', 'name': 'WS Stone Type'})
        cls.stone_shade = cls.env['pdp.stone.shade'].create({'code': 'WSH', 'shade': 'WS Shade'})
        cls.stone_shape = cls.env['pdp.stone.shape'].create({'code': 'WSP', 'shape': 'WS Shape'})
        cls.stone_size = cls.env['pdp.stone.size'].create({'name': 'WS-1.0'})
        cls.stone = cls.env['pdp.stone'].create({
            'code': 'WSTYWSH-WSP-WS-1.0',
            'type_id': cls.stone_type.id,
            'shade_id': cls.stone_shade.id,
            'shape_id': cls.stone_shape.id,
            'size_id': cls.stone_size.id,
        })

    def _base_payload(self, **extra):
        payload = {
            'model_id': self.model.id,
            'product_id': self.product.id,
            'composition_id': self.product.stone_composition_id.id or False,
            'deleted': {},
        }
        payload.update(extra)
        return payload

    def test_create_collections_returns_new_ids(self):
        """New rows are created and their db ids are returned, keyed by client _key."""
        res = self.svc.save_product_workspace(self._base_payload(
            parts=[{'id': None, 'key': -1, 'part_id': self.part_type.id, 'quantity': 4}],
            addons=[{'id': None, 'key': -2, 'addon_id': self.addon_type.id,
                     'cost': 10.0, 'currency_id': self.currency.id}],
            labor_product=[{'id': None, 'key': -3, 'labor_id': self.labor_type.id,
                            'cost': 20.0, 'currency_id': self.currency.id}],
            metals=[{'id': None, 'key': -4, 'metal_id': self.metal.id,
                     'purity_id': self.purity.id, 'weight': 2.5, 'metal_version': 'W'}],
        ))

        new_part_id = res['new_ids']['parts']['-1']
        self.assertTrue(new_part_id)
        self.assertEqual(self.env['pdp.product.part'].browse(new_part_id).quantity, 4)
        self.assertTrue(res['new_ids']['addons']['-2'])
        self.assertTrue(res['new_ids']['labor_product']['-3'])
        metal_id = res['new_ids']['metals']['-4']
        self.assertEqual(self.env['pdp.product.model.metal'].browse(metal_id).model_id, self.model)

    def test_update_existing_row(self):
        """A row carrying an id is written, not duplicated."""
        part = self.env['pdp.product.part'].create({
            'product_id': self.product.id, 'part_id': self.part_type.id, 'quantity': 1,
        })
        before = self.env['pdp.product.part'].search_count([('product_id', '=', self.product.id)])

        res = self.svc.save_product_workspace(self._base_payload(
            parts=[{'id': part.id, 'key': part.id, 'part_id': self.part_type.id, 'quantity': 9}],
        ))

        self.assertEqual(res['new_ids'], {})
        self.assertEqual(part.quantity, 9)
        self.assertEqual(
            self.env['pdp.product.part'].search_count([('product_id', '=', self.product.id)]),
            before,
        )

    def test_delete_rows(self):
        """Ids listed under `deleted` are unlinked."""
        part = self.env['pdp.product.part'].create({
            'product_id': self.product.id, 'part_id': self.part_type.id, 'quantity': 1,
        })
        self.svc.save_product_workspace(self._base_payload(deleted={'part': [part.id]}))
        self.assertFalse(part.exists())

    def test_stones_create_composition_lazily(self):
        """A product with no composition gets one created and linked when a stone is saved."""
        self.assertFalse(self.product.stone_composition_id)

        res = self.svc.save_product_workspace(self._base_payload(
            stones=[{'id': None, 'key': -7, 'stone_id': self.stone.id, 'pieces': 3,
                     'weight': 1.0, 'reshaped_weight': 0, 'setting': 0,
                     'setting_type_id': False, 'reshaped_shape_id': False,
                     'reshaped_size_id': False, 'line_num': ''}],
        ))

        self.assertTrue(res['composition_id'])
        self.product.invalidate_recordset(['stone_composition_id'])
        self.assertEqual(self.product.stone_composition_id.id, res['composition_id'])
        stone_id = res['new_ids']['stones']['-7']
        self.assertEqual(self.env['pdp.product.stone'].browse(stone_id).pieces, 3)

    def test_save_is_atomic_on_error(self):
        """If a later row fails, an earlier successful create is rolled back too."""
        before = self.env['pdp.product.model.metal'].search_count([('model_id', '=', self.model.id)])

        bad_payload = self._base_payload(
            # processed early — valid
            metals=[{'id': None, 'key': -8, 'metal_id': self.metal.id,
                     'purity_id': self.purity.id, 'weight': 1.0, 'metal_version': 'W'}],
            # processed last — invalid field forces create() to raise
            parts=[{'id': None, 'key': -9, 'part_id': self.part_type.id,
                    'quantity': 1, 'no_such_field_zzz': 1}],
        )

        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.svc.save_product_workspace(bad_payload)

        after = self.env['pdp.product.model.metal'].search_count([('model_id', '=', self.model.id)])
        self.assertEqual(before, after, "the valid metal create must roll back with the failed save")
