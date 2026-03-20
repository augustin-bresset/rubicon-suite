from odoo.tests.common import TransactionCase


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
        result = self.cat.get_user_uom(user_id=self.user.id)
        self.assertEqual(result, self.gram)

    def test_get_user_uom_falls_back_to_reference(self):
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
        with self.assertRaises(Exception):
            self.env['rubicon.uom.user.pref'].create({
                'user_id': self.user.id,
                'category_id': self.cat.id,
                'uom_id': self.troy_oz.id,
            })

    def test_set_global_default_atomic(self):
        self.troy_oz.set_global_default()
        self.assertTrue(self.troy_oz.is_global_default)
        self.assertFalse(self.gram.is_global_default)
