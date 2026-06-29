from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestColorCode(TransactionCase):
    """Colour code computation and center-stone rules (Lot 1)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Isolated stone types with codes that do NOT collide with the seed
        # pdp.stone.type.csv. Codes are picked so that ALPHABETICAL order is the
        # OPPOSITE of the weight order, proving the ordering is driven by weight.
        cls.size = cls.env['pdp.stone.size'].create({'name': '1.0CC'})
        cls.t_heavy = cls.env['pdp.stone.type'].create({'code': 'ZRU', 'name': 'Heavy CC'})
        cls.t_light = cls.env['pdp.stone.type'].create({'code': 'ADIA', 'name': 'Light CC'})
        cls.t_aaa = cls.env['pdp.stone.type'].create({'code': 'ZTAAA', 'name': 'Tie A CC'})
        cls.t_bbb = cls.env['pdp.stone.type'].create({'code': 'ZTBBB', 'name': 'Tie B CC'})

        cls.s_heavy = cls._stone(cls, cls.t_heavy, 'ZRU-CC')
        cls.s_light = cls._stone(cls, cls.t_light, 'ADIA-CC')
        cls.s_aaa = cls._stone(cls, cls.t_aaa, 'ZTAAA-CC')
        cls.s_bbb = cls._stone(cls, cls.t_bbb, 'ZTBBB-CC')

        cls.model = cls.env['pdp.product.model'].create({'code': 'ZMODCC1'})

    def _stone(self, stone_type, code):
        return self.env['pdp.stone'].create({
            'code': code,
            'type_id': stone_type.id,
            'size_id': self.size.id,
        })

    def _comp(self, code):
        return self.env['pdp.product.stone.composition'].create({'code': code})

    def _line(self, comp, stone, weight, pieces=1, reshaped=0.0, center=False):
        return self.env['pdp.product.stone'].create({
            'composition_id': comp.id,
            'stone_id': stone.id,
            'pieces': pieces,
            'weight': weight,
            'reshaped_weight': reshaped,
            'is_center': center,
        })

    # ------------------------------------------------------------------ basics

    def test_empty_composition(self):
        comp = self._comp('C-EMPTY')
        self.assertEqual(comp.compute_color_code(), '')

    def test_single_type(self):
        comp = self._comp('C-SINGLE')
        self._line(comp, self.s_light, weight=0.5)
        self.assertEqual(comp.compute_color_code(), 'ADIA')

    def test_distinct_types_dedup(self):
        """Several lines of the same type collapse to a single code."""
        comp = self._comp('C-DEDUP')
        self._line(comp, self.s_light, weight=0.5, pieces=1)
        self._line(comp, self.s_light, weight=0.3, pieces=2)
        self._line(comp, self.s_light, weight=0.7, pieces=1)
        self.assertEqual(comp.compute_color_code(), 'ADIA')

    # ------------------------------------------------------- ordering by weight

    def test_order_by_heaviest_single_stone(self):
        """Witness example: 3 light@0.5 + 1 heavy@1.0 + 5 heavy@0.2 -> heavy first.

        Maps to the user's '3 diamants 0.5 + 1 rubis 1ct + 5 rubis 0.2 -> RU+DTS'.
        ZRU (max single 1.0) outranks ADIA (max single 0.5), even though ADIA
        sorts first alphabetically -> proves weight drives the order.
        """
        comp = self._comp('C-WITNESS')
        self._line(comp, self.s_light, weight=0.5, pieces=3)
        self._line(comp, self.s_heavy, weight=1.0, pieces=1)
        self._line(comp, self.s_heavy, weight=0.2, pieces=5)
        self.assertEqual(comp.compute_color_code(), 'ZRU+ADIA')

    def test_tie_break_alphabetical(self):
        """Equal max weight -> deterministic alphabetical type-code order."""
        comp = self._comp('C-TIE')
        self._line(comp, self.s_bbb, weight=1.0)
        self._line(comp, self.s_aaa, weight=1.0)
        self.assertEqual(comp.compute_color_code(), 'ZTAAA+ZTBBB')

    def test_reshaped_weight_takes_precedence(self):
        """Reshaped weight, when present, is used instead of original weight."""
        comp = self._comp('C-RESHAPE')
        # ADIA original 0.5 but reshaped up to 2.0 -> beats ZRU at 1.0
        self._line(comp, self.s_light, weight=0.5, reshaped=2.0)
        self._line(comp, self.s_heavy, weight=1.0)
        self.assertEqual(comp.compute_color_code(), 'ADIA+ZRU')

    # ----------------------------------------------------------- center stone

    def test_center_overrides_order(self):
        """A designated center stone's type is placed first regardless of weight."""
        comp = self._comp('C-CENTER')
        self._line(comp, self.s_light, weight=0.5, center=True)  # lighter, but center
        self._line(comp, self.s_heavy, weight=1.0)
        self.assertEqual(comp.compute_color_code(), 'ADIA+ZRU')

    def test_center_with_three_types(self):
        comp = self._comp('C-CENTER3')
        self._line(comp, self.s_aaa, weight=0.1, center=True)  # center, lightest
        self._line(comp, self.s_heavy, weight=1.0)
        self._line(comp, self.s_light, weight=0.5)
        # center first, then remaining by weight desc
        self.assertEqual(comp.compute_color_code(), 'ZTAAA+ZRU+ADIA')

    def test_single_center_constraint(self):
        """At most one center stone per composition."""
        comp = self._comp('C-DOUBLE-CENTER')
        self._line(comp, self.s_heavy, weight=1.0, center=True)
        with self.assertRaises(ValidationError):
            with self.env.cr.savepoint():
                self._line(comp, self.s_light, weight=0.5, center=True)

    def test_center_isolated_per_composition(self):
        """Two compositions may each have their own center stone."""
        c1 = self._comp('C-ISO-1')
        self._line(c1, self.s_heavy, weight=1.0, center=True)
        c2 = self._comp('C-ISO-2')
        self._line(c2, self.s_light, weight=0.5, center=True)
        self.assertEqual(c1.compute_color_code(), 'ZRU')
        self.assertEqual(c2.compute_color_code(), 'ADIA')

    # --------------------------------------------------------- code builders

    def test_build_composition_code(self):
        Comp = self.env['pdp.product.stone.composition']
        self.assertEqual(Comp.build_composition_code('M1', 'ZRU+ADIA'), 'M1-ZRU+ADIA')
        self.assertEqual(Comp.build_composition_code('M1', ''), 'M1')

    def test_build_product_code(self):
        Comp = self.env['pdp.product.stone.composition']
        self.assertEqual(Comp.build_product_code('M1', 'ZRU+ADIA', 'W'), 'M1-ZRU+ADIA/W')
        self.assertEqual(Comp.build_product_code('M1', 'ZRU+ADIA', ''), 'M1-ZRU+ADIA')
        self.assertEqual(Comp.build_product_code('M1', '', 'W'), 'M1/W')

    # --------------------------------------------------- product-level helpers

    def test_product_suggested_code(self):
        comp = self._comp('C-PROD')
        self._line(comp, self.s_light, weight=0.5, pieces=3)
        self._line(comp, self.s_heavy, weight=1.0)
        product = self.env['pdp.product'].create({
            'code': 'LEGACY-PROD-01',
            'model_id': self.model.id,
            'metal': 'W',
            'stone_composition_id': comp.id,
        })
        self.assertEqual(product.compute_color_code(), 'ZRU+ADIA')
        self.assertEqual(product.compute_suggested_code(), 'ZMODCC1-ZRU+ADIA/W')

    def test_product_without_composition(self):
        product = self.env['pdp.product'].create({
            'code': 'LEGACY-PROD-02',
            'model_id': self.model.id,
            'metal': 'W',
        })
        self.assertEqual(product.compute_color_code(), '')
        self.assertEqual(product.compute_suggested_code(), 'ZMODCC1/W')

    # ------------------------------------------ stateless line-data (workspace)

    def test_color_code_from_line_data(self):
        Comp = self.env['pdp.product.stone.composition']
        line_data = [
            {'type_id': self.t_light.id, 'weight': 0.5},
            {'type_id': self.t_heavy.id, 'weight': 1.0},
            {'type_id': self.t_heavy.id, 'weight': 0.2},
        ]
        self.assertEqual(Comp.color_code_from_line_data(line_data), 'ZRU+ADIA')

    def test_color_code_from_line_data_uses_reshaped(self):
        Comp = self.env['pdp.product.stone.composition']
        line_data = [
            {'type_id': self.t_light.id, 'weight': 0.5, 'reshaped_weight': 2.0},
            {'type_id': self.t_heavy.id, 'weight': 1.0, 'reshaped_weight': 0.0},
        ]
        self.assertEqual(Comp.color_code_from_line_data(line_data), 'ADIA+ZRU')

    def test_color_code_from_line_data_center(self):
        Comp = self.env['pdp.product.stone.composition']
        line_data = [
            {'type_id': self.t_light.id, 'weight': 0.5, 'is_center': True},
            {'type_id': self.t_heavy.id, 'weight': 1.0},
        ]
        self.assertEqual(Comp.color_code_from_line_data(line_data), 'ADIA+ZRU')

    def test_color_code_from_line_data_empty_and_typeless(self):
        Comp = self.env['pdp.product.stone.composition']
        self.assertEqual(Comp.color_code_from_line_data([]), '')
        self.assertEqual(Comp.color_code_from_line_data([{'weight': 1.0}]), '')

    def test_suggest_from_line_data(self):
        Comp = self.env['pdp.product.stone.composition']
        line_data = [
            {'type_id': self.t_heavy.id, 'weight': 1.0},
            {'type_id': self.t_light.id, 'weight': 0.5},
        ]
        res = Comp.suggest_from_line_data(line_data, 'ZMODCC1', 'W')
        self.assertEqual(res['colors'], 'ZRU+ADIA')
        self.assertEqual(res['product_code'], 'ZMODCC1-ZRU+ADIA/W')
