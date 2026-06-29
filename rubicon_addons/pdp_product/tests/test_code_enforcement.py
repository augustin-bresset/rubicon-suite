from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestCodeEnforcement(TransactionCase):
    """Unique product codes and the apply-suggested-code action (Lot 4)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.model = cls.env['pdp.product.model'].create({'code': 'ZENF1'})
        cls.size = cls.env['pdp.stone.size'].create({'name': 'ENF-1.0'})
        cls.t_a = cls.env['pdp.stone.type'].create({'code': 'ZENFA', 'name': 'Enf A'})
        cls.t_b = cls.env['pdp.stone.type'].create({'code': 'ZENFB', 'name': 'Enf B'})
        cls.s_a = cls.env['pdp.stone'].create(
            {'code': 'ZENFA-S', 'type_id': cls.t_a.id, 'size_id': cls.size.id})
        cls.s_b = cls.env['pdp.stone'].create(
            {'code': 'ZENFB-S', 'type_id': cls.t_b.id, 'size_id': cls.size.id})

    def _comp_with(self, code, lines):
        comp = self.env['pdp.product.stone.composition'].create({'code': code})
        for stone, weight in lines:
            self.env['pdp.product.stone'].create({
                'composition_id': comp.id, 'stone_id': stone.id,
                'pieces': 1, 'weight': weight,
            })
        return comp

    # ------------------------------------------------------------ uniqueness

    def test_uniqueness_blocks_duplicate_code(self):
        self.env['pdp.product'].create({'code': 'ZENF-UNIQ-1', 'model_id': self.model.id})
        with self.assertRaises(ValidationError):
            with self.env.cr.savepoint():
                self.env['pdp.product'].create({'code': 'ZENF-UNIQ-1', 'model_id': self.model.id})

    def test_uniqueness_allows_distinct_codes(self):
        a = self.env['pdp.product'].create({'code': 'ZENF-UNIQ-2', 'model_id': self.model.id})
        b = self.env['pdp.product'].create({'code': 'ZENF-UNIQ-3', 'model_id': self.model.id})
        self.assertNotEqual(a.code, b.code)

    # ------------------------------------------------------- apply suggested

    def test_apply_sets_code_archives_and_aligns_composition(self):
        comp = self._comp_with('ZENF1-TMP', [(self.s_a, 1.0), (self.s_b, 0.5)])
        product = self.env['pdp.product'].create({
            'code': 'TMP-APPLY-1', 'model_id': self.model.id, 'metal': 'W',
            'stone_composition_id': comp.id,
        })
        product.apply_suggested_code()
        self.assertEqual(product.code, 'ZENF1-ZENFA+ZENFB/W')
        self.assertEqual(product.legacy_code, 'TMP-APPLY-1')
        self.assertEqual(product.stone_composition_id.code, 'ZENF1-ZENFA+ZENFB')

    def test_apply_is_noop_when_already_matching(self):
        comp = self._comp_with('ZENF1-ZENFA', [(self.s_a, 1.0)])
        product = self.env['pdp.product'].create({
            'code': 'ZENF1-ZENFA/W', 'model_id': self.model.id, 'metal': 'W',
            'stone_composition_id': comp.id,
        })
        self.assertEqual(product.apply_suggested_code(), 'ZENF1-ZENFA/W')
        self.assertFalse(product.legacy_code)

    def test_apply_collision_raises(self):
        # Another product already occupies the structured code.
        self.env['pdp.product'].create({
            'code': 'ZENF1-ZENFA/W', 'model_id': self.model.id, 'metal': 'W',
        })
        comp = self._comp_with('ZENF1-TMP2', [(self.s_a, 1.0)])
        product = self.env['pdp.product'].create({
            'code': 'TMP-APPLY-2', 'model_id': self.model.id, 'metal': 'W',
            'stone_composition_id': comp.id,
        })
        with self.assertRaises(UserError):
            with self.env.cr.savepoint():
                product.apply_suggested_code()
        self.assertEqual(product.code, 'TMP-APPLY-2')  # unchanged

    def test_apply_empty_suggestion_raises(self):
        product = self.env['pdp.product'].create({'code': 'NOMODEL-APPLY'})
        with self.assertRaises(UserError):
            with self.env.cr.savepoint():
                product.apply_suggested_code()
