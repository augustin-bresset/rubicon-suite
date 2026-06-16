from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.tools import mute_logger
from psycopg2 import IntegrityError


class TestRubiconUomCategory(TransactionCase):

    def test_create_category(self):
        cat = self.env['rubicon.uom.category'].create({
            'name': 'Test Weight',
            'code': 'test_weight',
        })
        self.assertEqual(cat.code, 'test_weight')
        # _rec_name='code' means display_name == code value
        self.assertEqual(cat.display_name, 'test_weight')

    def test_code_unique(self):
        self.env['rubicon.uom.category'].create({'name': 'A', 'code': 'unique_test'})
        with self.assertRaises(Exception):
            self.env['rubicon.uom.category'].create({'name': 'B', 'code': 'unique_test'})


class TestRubiconUomConversion(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cat = cls.env['rubicon.uom.category'].create({
            'name': 'Metal Weight', 'code': 'metal_weight',
        })
        cls.cat2 = cls.env['rubicon.uom.category'].create({
            'name': 'Stone Weight', 'code': 'stone_weight',
        })
        cls.gram = cls.env['rubicon.uom'].create({
            'name': 'Gramme', 'symbol': 'g',
            'category_id': cls.cat.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })
        cls.troy_oz = cls.env['rubicon.uom'].create({
            'name': 'Troy Ounce', 'symbol': 'oz t',
            'category_id': cls.cat.id,
            'ratio': 31.1035, 'is_reference': False, 'is_global_default': False,
        })
        cls.carat = cls.env['rubicon.uom'].create({
            'name': 'Carat', 'symbol': 'ct',
            'category_id': cls.cat2.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })

    def test_convert_g_to_troy_oz(self):
        result = self.gram.convert(62.207, self.troy_oz)
        self.assertAlmostEqual(result, 2.0, places=3)

    def test_convert_troy_oz_to_g(self):
        result = self.troy_oz.convert(2.0, self.gram)
        self.assertAlmostEqual(result, 62.207, places=2)

    def test_round_trip(self):
        original = 42.5
        via_troy = self.gram.convert(original, self.troy_oz)
        back = self.troy_oz.convert(via_troy, self.gram)
        self.assertAlmostEqual(back, original, places=6)

    def test_convert_zero_returns_zero(self):
        self.assertEqual(self.gram.convert(0, self.troy_oz), 0)

    def test_convert_none_returns_zero(self):
        self.assertEqual(self.gram.convert(None, self.troy_oz), 0)

    def test_convert_negative_allowed(self):
        result = self.gram.convert(-10.0, self.troy_oz)
        self.assertAlmostEqual(result, -10.0 / 31.1035, places=6)

    def test_cross_category_raises(self):
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            self.gram.convert(10.0, self.carat)


class TestRubiconUomUserPref(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cat = cls.env['rubicon.uom.category'].create({
            'name': 'Metal Weight', 'code': 'mw_pref_test',
        })
        cls.cat2 = cls.env['rubicon.uom.category'].create({
            'name': 'Stone Weight', 'code': 'sw_pref_test',
        })
        cls.gram = cls.env['rubicon.uom'].create({
            'name': 'Gramme', 'symbol': 'g', 'category_id': cls.cat.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })
        cls.troy_oz = cls.env['rubicon.uom'].create({
            'name': 'Troy Oz', 'symbol': 'oz t', 'category_id': cls.cat.id,
            'ratio': 31.1035, 'is_reference': False, 'is_global_default': False,
        })
        cls.carat = cls.env['rubicon.uom'].create({
            'name': 'Carat', 'symbol': 'ct', 'category_id': cls.cat2.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })
        cls.user = cls.env.ref('base.user_demo')

    def test_get_user_uom_returns_user_pref(self):
        self.env['rubicon.uom.user.pref'].create({
            'user_id': self.user.id,
            'category_id': self.cat.id,
            'uom_id': self.troy_oz.id,
        })
        result = self.cat.get_user_uom(user_id=self.user.id)
        self.assertEqual(result, self.troy_oz)

    def test_get_user_uom_falls_back_to_global_default(self):
        # Ensure no pref exists for this user (TransactionCase rolls back each test)
        self.assertEqual(self.env['rubicon.uom.user.pref'].search_count([
            ('user_id', '=', self.user.id),
            ('category_id', '=', self.cat.id),
        ]), 0)
        result = self.cat.get_user_uom(user_id=self.user.id)
        self.assertEqual(result, self.gram)

    def test_get_user_uom_falls_back_to_reference(self):
        # Ensure no pref exists for this user (TransactionCase rolls back each test)
        self.assertEqual(self.env['rubicon.uom.user.pref'].search_count([
            ('user_id', '=', self.user.id),
            ('category_id', '=', self.cat.id),
        ]), 0)
        # No global default — gram is reference only.
        # Safe to mutate self.gram here: Odoo TransactionCase wraps each test_*
        # method in a savepoint that is rolled back after the test, so this
        # write does not affect other test methods.
        self.gram.write({'is_global_default': False})
        result = self.cat.get_user_uom(user_id=self.user.id)
        self.assertEqual(result, self.gram)  # is_reference=True

    def test_delete_pref_reverts_to_global_default(self):
        pref = self.env['rubicon.uom.user.pref'].create({
            'user_id': self.user.id,
            'category_id': self.cat.id,
            'uom_id': self.troy_oz.id,
        })
        self.assertEqual(self.cat.get_user_uom(user_id=self.user.id), self.troy_oz)
        pref.unlink()
        self.assertEqual(self.cat.get_user_uom(user_id=self.user.id), self.gram)

    def test_uom_must_belong_to_category(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['rubicon.uom.user.pref'].create({
                'user_id': self.user.id,
                'category_id': self.cat.id,
                'uom_id': self.carat.id,  # belongs to cat2, not cat
            })

    def test_unique_per_user_category(self):
        self.env['rubicon.uom.user.pref'].create({
            'user_id': self.user.id,
            'category_id': self.cat.id,
            'uom_id': self.gram.id,
        })
        with self.assertRaises(IntegrityError):
            with mute_logger('odoo.sql_db'):
                self.env['rubicon.uom.user.pref'].create({
                    'user_id': self.user.id,
                    'category_id': self.cat.id,
                    'uom_id': self.troy_oz.id,
                })
                self.env.flush_all()  # force the SQL to execute and trigger the constraint

    def test_set_global_default_atomic(self):
        self.troy_oz.set_global_default()
        self.assertTrue(self.troy_oz.is_global_default)
        self.assertFalse(self.gram.is_global_default)


class TestStandardOunceMetalCost(TransactionCase):
    """Introduce the standard (avoirdupois) ounce and reproduce the legacy
    metal cost from meta/pdp/smoke_test.md through rubicon_uom.

    R132's metal line was 758.45 in the old PDP capture, priced per *standard*
    ounce (28.349523125 g). The current engine prices per *troy* ounce
    (31.1034768 g), giving 690.69. Adding the standard ounce as a unit and
    converting through rubicon_uom must yield each figure for its own unit —
    a check against an externally-sourced value, not a snapshot of our output,
    and an exercise of the uom module on a real pricing basis.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mass = cls.env['rubicon.uom.category'].create({
            'name': 'Metal Weight', 'code': 'mw_oz_test',
        })
        cls.gram = cls.env['rubicon.uom'].create({
            'name': 'Gramme', 'symbol': 'g', 'category_id': cls.mass.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })
        cls.troy_oz = cls.env['rubicon.uom'].create({
            'name': 'Troy Ounce', 'symbol': 'oz t', 'category_id': cls.mass.id,
            'ratio': 31.1034768,
        })
        # The unit being introduced: the standard (avoirdupois) ounce.
        cls.std_oz = cls.env['rubicon.uom'].create({
            'name': 'Standard Ounce', 'symbol': 'oz', 'category_id': cls.mass.id,
            'ratio': 28.349523125,
        })

    def test_standard_ounce_conversion(self):
        # 1 standard ounce == 28.349523125 g, and back.
        self.assertAlmostEqual(self.std_oz.convert(1.0, self.gram), 28.349523125, places=6)
        self.assertAlmostEqual(self.gram.convert(28.349523125, self.std_oz), 1.0, places=6)

    def test_metal_cost_basis_matches_smoke_test(self):
        # R132 white gold: 3255 $/oz, 8.8 g alloy, 18K = 75% pure (smoke_test.md).
        cost_per_oz = 3255.0
        pure_grams = 8.8 * 0.75

        cost_standard = cost_per_oz * self.gram.convert(pure_grams, self.std_oz)  # ~757.8
        cost_troy = cost_per_oz * self.gram.convert(pure_grams, self.troy_oz)     # 690.69

        # Standard ounce reproduces the legacy capture (758.45) within screenshot rounding.
        self.assertAlmostEqual(cost_standard, 758.45, delta=1.0)
        # Troy ounce reproduces the current engine figure exactly.
        self.assertAlmostEqual(cost_troy, 690.69, delta=0.1)
        # Pricing per standard ounce is heavier than per (larger) troy ounce.
        self.assertGreater(cost_standard, cost_troy)
