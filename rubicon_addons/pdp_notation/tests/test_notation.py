from odoo.tests.common import TransactionCase


class TestNotation(TransactionCase):
    """Grammar PP[G][BB][EE]: build, parse, transcribe, verify."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.size = env['pdp.stone.size'].create({'name': 'ZNT-1.0'})
        cls.shape_rd = env['pdp.stone.shape'].create(
            {'code': 'ZNRD', 'shape': 'Znt Round'})
        cls.shape_ps = env['pdp.stone.shape'].create(
            {'code': 'ZNPS', 'shape': 'Znt Pear'})
        cls.sh_default = env['pdp.stone.shade'].create(
            {'code': 'ZND', 'shade': 'Znt Default'})
        cls.sh_grade = env['pdp.stone.shade'].create(
            {'code': 'ZNG', 'shade': 'Znt Light'})
        cls.sh_hue = env['pdp.stone.shade'].create(
            {'code': 'ZNH', 'shade': 'Znt Pink'})
        cls.sh_fused = env['pdp.stone.shade'].create(
            {'code': 'ZNF', 'shade': 'Znt Pink Light'})
        cls.t_plain = env['pdp.stone.type'].create(
            {'code': 'ZNTA', 'name': 'Znt Plain'})
        cls.t_colour = env['pdp.stone.type'].create(
            {'code': 'ZNTB', 'name': 'Znt Blue Something'})

        cls.hue = env['pdp.notation.hue'].create({'code': '9Z', 'name': 'Znt Pink'})
        cls.hue_blue = env['pdp.notation.hue'].create({'code': '8Z', 'name': 'Znt Blue'})
        cls.grade = env['pdp.notation.grade'].create({'code': '7', 'name': 'Znt Light'})
        cls.art_plain = env['pdp.notation.stone'].create({
            'code': 'ZA', 'type_id': cls.t_plain.id,
            'default_shade_id': cls.sh_default.id,
            'default_shape_id': cls.shape_rd.id,
        })
        cls.art_colour = env['pdp.notation.stone'].create({
            'code': 'ZB', 'type_id': cls.t_colour.id,
            'implied_hue_id': cls.hue_blue.id,
            'default_shape_id': cls.shape_rd.id,
        })
        env['pdp.notation.shape'].create(
            {'code': 'ZP', 'shape_id': cls.shape_ps.id})
        Map = env['pdp.notation.shade.map']
        Map.create({'shade_id': cls.sh_grade.id, 'grade_id': cls.grade.id})
        Map.create({'shade_id': cls.sh_hue.id, 'hue_id': cls.hue.id})
        Map.create({'shade_id': cls.sh_fused.id,
                    'grade_id': cls.grade.id, 'hue_id': cls.hue.id})
        cls.service = env['pdp.notation']

    def _stone(self, type_rec, shade=None, shape=None):
        return self.env['pdp.stone'].create({
            'code': f"ZNS-{type_rec.code}-{shade.code if shade else 'X'}-"
                    f"{shape.code if shape else 'X'}",
            'type_id': type_rec.id, 'size_id': self.size.id,
            'shade_id': shade.id if shade else False,
            'shape_id': shape.id if shape else False,
        })

    # ---------------------------------------------------------- build

    def test_build_omits_defaults(self):
        built = self.service.build_token(
            self.t_plain.id, self.sh_default.id, self.shape_rd.id)
        self.assertEqual(built['token'], 'ZA')
        self.assertFalse(built['problems'])

    def test_build_every_block_combination(self):
        cases = [
            (None, None, 'ZA'),
            (self.sh_grade, None, 'ZA7'),
            (self.sh_hue, None, 'ZA9Z'),
            (self.sh_fused, None, 'ZA79Z'),
            (None, self.shape_ps, 'ZAZP'),
            (self.sh_grade, self.shape_ps, 'ZA7ZP'),
            (self.sh_hue, self.shape_ps, 'ZA9ZZP'),
            (self.sh_fused, self.shape_ps, 'ZA79ZZP'),
        ]
        for shade, shape, expected in cases:
            built = self.service.build_token(
                self.t_plain.id, shade.id if shade else None,
                shape.id if shape else None)
            self.assertEqual(built['token'], expected)
            self.assertFalse(built['problems'], expected)

    def test_build_refuses_double_colour(self):
        built = self.service.build_token(self.t_colour.id, self.sh_hue.id)
        self.assertTrue(any('double colour' in p for p in built['problems']))

    def test_build_reports_unmapped(self):
        no_article = self.env['pdp.stone.type'].create(
            {'code': 'ZNTC', 'name': 'Znt Unmapped'})
        built = self.service.build_token(no_article.id)
        self.assertIn('no article', built['problems'][0])
        self.assertEqual(built['token'], '?ZNTC?')

    # ---------------------------------------------------------- parse

    def test_parse_round_trip(self):
        for token in ('ZA', 'ZA7', 'ZA9Z', 'ZA79Z', 'ZAZP', 'ZA7ZP',
                      'ZA9ZZP', 'ZA79ZZP'):
            parsed = self.service.parse_token(token)
            self.assertFalse(parsed['problems'], token)
            self.assertEqual(parsed['type_id'], self.t_plain.id, token)

    def test_parse_resolves_legacy_records(self):
        parsed = self.service.parse_token('ZA79Z')
        self.assertEqual(parsed['shade_id'], self.sh_fused.id)
        self.assertEqual(parsed['shape_id'], self.shape_rd.id)  # default
        parsed = self.service.parse_token('ZAZP')
        self.assertEqual(parsed['shade_id'], self.sh_default.id)
        self.assertEqual(parsed['shape_id'], self.shape_ps.id)

    def test_parse_rejects_bad_structures(self):
        for bad in ('Z', 'ZAABC', 'ZA7Z', 'ZA123'):
            self.assertTrue(self.service.parse_token(bad)['problems'], bad)

    def test_parse_flags_double_colour(self):
        parsed = self.service.parse_token('ZB9Z')
        self.assertTrue(any('double colour' in p for p in parsed['problems']))

    # ------------------------------------------------ transcribe & verify

    def _product_with(self, lines):
        comp = self.env['pdp.product.stone.composition'].create(
            {'code': 'ZNT-COMP-%d' % len(lines)})
        for stone, weight, is_center in lines:
            self.env['pdp.product.stone'].create({
                'composition_id': comp.id, 'stone_id': stone.id,
                'pieces': 1, 'weight': weight, 'is_center': is_center,
            })
        model = self.env['pdp.product.model'].create(
            {'code': 'ZNTM%d' % len(lines)})
        return self.env['pdp.product'].create({
            'code': 'ZNTM%d-X/W' % len(lines), 'model_id': model.id,
            'metal': 'W', 'active': True,
            'stone_composition_id': comp.id,
        })

    def test_transcription_follows_the_established_order(self):
        light = self._stone(self.t_plain, self.sh_grade)
        heavy = self._stone(self.t_colour)
        center = self._stone(self.t_plain, self.sh_hue, self.shape_ps)
        product = self._product_with(
            [(light, 2.0, False), (heavy, 5.0, False), (center, 0.5, True)])
        result = self.service.transcribe_product(product.id)
        # center first, then by heaviest single stone descending
        self.assertEqual(result['code'], 'ZA9ZZP+ZB+ZA7')
        self.assertFalse(result['problems'])

    def test_verify_accepts_the_coherent_code(self):
        stone = self._stone(self.t_plain, self.sh_grade)
        product = self._product_with([(stone, 1.0, False)])
        verdict = self.service.verify_product(product.id, 'ZA7')
        self.assertTrue(verdict['ok'], verdict['problems'])

    def test_verify_flags_wrong_order_and_wrong_stones(self):
        a = self._stone(self.t_plain, self.sh_grade)
        b = self._stone(self.t_colour)
        product = self._product_with([(a, 5.0, False), (b, 1.0, False)])
        wrong_order = self.service.verify_product(product.id, 'ZB+ZA7')
        self.assertFalse(wrong_order['ok'])
        self.assertTrue(any('order' in p for p in wrong_order['problems']))
        wrong_stone = self.service.verify_product(product.id, 'ZA7+ZA9Z')
        self.assertFalse(wrong_stone['ok'])
        self.assertTrue(any('do not match' in p for p in wrong_stone['problems']))

    def test_lookup_both_directions(self):
        found = self.service.lookup('Znt Plain')
        self.assertIn(('ZA', 'ZNTA', 'Znt Plain'), found['stones'])
        found = self.service.lookup('ZA')
        self.assertTrue(found['stones'])
