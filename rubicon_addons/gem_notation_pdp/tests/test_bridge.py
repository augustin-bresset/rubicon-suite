from odoo.tests.common import TransactionCase


class TestBridge(TransactionCase):
    """Legacy PDP records to notation tokens: transcription and verdicts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.size = env['pdp.stone.size'].create({'name': 'ZNB-1.0'})
        cls.shape_rd = env['pdp.stone.shape'].create(
            {'code': 'ZBRD', 'shape': 'Znb Round'})
        cls.shape_ps = env['pdp.stone.shape'].create(
            {'code': 'ZBPS', 'shape': 'Znb Pear'})
        cls.sh_grade = env['pdp.stone.shade'].create(
            {'code': 'ZBG', 'shade': 'Znb Light'})
        cls.sh_fused = env['pdp.stone.shade'].create(
            {'code': 'ZBF', 'shade': 'Znb Pink Light'})
        cls.sh_unmapped = env['pdp.stone.shade'].create(
            {'code': 'ZBU', 'shade': 'Znb Mystery'})
        cls.t_plain = env['pdp.stone.type'].create(
            {'code': 'ZNBA', 'name': 'Znb Plain'})
        cls.t_colour = env['pdp.stone.type'].create(
            {'code': 'ZNBB', 'name': 'Znb Blue Something'})

        cls.grade = env['gem.notation.grade'].create(
            {'code': '9', 'name': 'Znb Light'})
        cls.hue = env['gem.notation.hue'].create(
            {'code': '9Z', 'name': 'Znb Pink'})
        cls.hue_blue = env['gem.notation.hue'].create(
            {'code': '8Z', 'name': 'Znb Blue'})
        cls.nshape_rd = env['gem.notation.shape'].create(
            {'code': 'ZR', 'name': 'Znb Round', 'shape_id': cls.shape_rd.id})
        cls.nshape_ps = env['gem.notation.shape'].create(
            {'code': 'ZP', 'name': 'Znb Pear', 'shape_id': cls.shape_ps.id})
        cls.art = env['gem.notation.stone'].create({
            'code': 'ZA', 'name': 'Znb Plain', 'type_id': cls.t_plain.id,
            'default_shape_id': cls.nshape_rd.id,
        })
        cls.art_colour = env['gem.notation.stone'].create({
            'code': 'ZB', 'name': 'Znb Blue Something',
            'type_id': cls.t_colour.id,
            'implied_hue_id': cls.hue_blue.id,
            'default_shape_id': cls.nshape_rd.id,
        })
        Map = env['gem.notation.shade.map']
        Map.create({'shade_id': cls.sh_grade.id, 'grade_id': cls.grade.id})
        Map.create({'shade_id': cls.sh_fused.id,
                    'grade_id': cls.grade.id, 'hue_id': cls.hue.id})
        cls.service = env['gem.notation']

    def _stone(self, type_rec, shade=None, shape=None):
        return self.env['pdp.stone'].create({
            'code': f"ZNB-{type_rec.code}-{shade.code if shade else 'X'}-"
                    f"{shape.code if shape else 'X'}",
            'type_id': type_rec.id, 'size_id': self.size.id,
            'shade_id': shade.id if shade else False,
            'shape_id': shape.id if shape else False,
        })

    def _product_with(self, lines):
        comp = self.env['pdp.product.stone.composition'].create(
            {'code': 'ZNB-COMP-%d' % len(lines)})
        for stone, weight, is_center in lines:
            self.env['pdp.product.stone'].create({
                'composition_id': comp.id, 'stone_id': stone.id,
                'pieces': 1, 'weight': weight, 'is_center': is_center,
            })
        model = self.env['pdp.product.model'].create(
            {'code': 'ZNBM%d' % len(lines)})
        return self.env['pdp.product'].create({
            'code': 'ZNBM%d-X/W' % len(lines), 'model_id': model.id,
            'metal': 'W', 'active': True,
            'stone_composition_id': comp.id,
        })

    def test_legacy_build_maps_and_omits_defaults(self):
        built = self.service.build_token_legacy(
            self.t_plain.id, self.sh_fused.id, self.shape_rd.id)
        self.assertEqual(built['token'], 'ZA99Z')  # default shape omitted
        self.assertFalse(built['problems'])
        built = self.service.build_token_legacy(
            self.t_plain.id, None, self.shape_ps.id)
        self.assertEqual(built['token'], 'ZAZP')

    def test_legacy_build_reports_gaps(self):
        built = self.service.build_token_legacy(
            self.t_plain.id, self.sh_unmapped.id)
        self.assertTrue(any('not mapped' in p for p in built['problems']))
        orphan = self.env['pdp.stone.type'].create(
            {'code': 'ZNBC', 'name': 'Znb Orphan'})
        built = self.service.build_token_legacy(orphan.id)
        self.assertEqual(built['token'], '?ZNBC?')

    def test_double_colour_via_fused_shade_on_colour_type(self):
        built = self.service.build_token_legacy(
            self.t_colour.id, self.sh_fused.id)
        self.assertTrue(any('double colour' in p for p in built['problems']))

    def test_transcription_follows_the_established_order(self):
        light = self._stone(self.t_plain, self.sh_grade)
        heavy = self._stone(self.t_colour)
        center = self._stone(self.t_plain, self.sh_fused, self.shape_ps)
        product = self._product_with(
            [(light, 2.0, False), (heavy, 5.0, False), (center, 0.5, True)])
        result = self.service.transcribe_product(product.id)
        self.assertEqual(result['code'], 'ZA99ZZP+ZB+ZA9')
        self.assertFalse(result['problems'])

    def test_proposals_give_everything_a_correspondence(self):
        blue_type = self.env['pdp.stone.type'].create(
            {'code': 'ZNBD', 'name': 'Blue Znbthing'})
        # some usage so the defaults phase has statistics
        stone = self._stone(self.t_plain, self.sh_grade)
        self._product_with([(stone, 1.0, False)])
        self.service.action_propose_codes()
        # every legacy shade is mapped — none left behind
        self.env.cr.execute("""
            SELECT count(*) FROM pdp_stone_shade sh
            WHERE NOT EXISTS (SELECT 1 FROM gem_notation_shade_map m
                              WHERE m.shade_id = sh.id)""")
        self.assertEqual(self.env.cr.fetchall()[0][0], 0)
        # the unmapped fixture shade became a hue mapping
        mapping = self.env['gem.notation.shade.map'].search(
            [('shade_id', '=', self.sh_unmapped.id)])
        self.assertTrue(mapping.hue_id)
        # a colour-bearing type name proposes the implied hue
        article = self.env['gem.notation.stone'].search(
            [('type_id', '=', blue_type.id)])
        self.assertEqual(article.implied_hue_id.name, 'Blue')
        # defaults follow usage: t_plain's modal shade is a grade
        self.assertEqual(self.art.default_grade_id, self.grade)
        # idempotent: a second run adds nothing
        again = self.service.action_propose_codes()
        for key in ('stones', 'shapes', 'hues', 'shade_maps', 'implied'):
            self.assertEqual(again[key], 0, key)

    def test_verify_verdicts(self):
        a = self._stone(self.t_plain, self.sh_grade)
        b = self._stone(self.t_colour)
        product = self._product_with([(a, 5.0, False), (b, 1.0, False)])
        good = self.service.verify_product(product.id, 'ZA9+ZB')
        self.assertTrue(good['ok'], good['problems'])
        wrong_order = self.service.verify_product(product.id, 'ZB+ZA9')
        self.assertFalse(wrong_order['ok'])
        self.assertTrue(any('order' in p for p in wrong_order['problems']))
        wrong_stone = self.service.verify_product(product.id, 'ZA9+ZA9Z')
        self.assertFalse(wrong_stone['ok'])
        self.assertTrue(any('do not match' in p
                            for p in wrong_stone['problems']))
