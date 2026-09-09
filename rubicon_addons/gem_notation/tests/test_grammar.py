from odoo.tests.common import TransactionCase


class TestGrammar(TransactionCase):
    """Grammar PP[G][BB][EE]: build, parse, order — pure notation records."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.grade = env['gem.notation.grade'].create(
            {'code': '7', 'name': 'Znt Light'})
        cls.hue = env['gem.notation.hue'].create(
            {'code': '9Z', 'name': 'Znt Pink'})
        cls.hue_blue = env['gem.notation.hue'].create(
            {'code': '8Z', 'name': 'Znt Blue'})
        cls.shape = env['gem.notation.shape'].create(
            {'code': 'ZP', 'name': 'Znt Pear'})
        cls.shape_rd = env['gem.notation.shape'].create(
            {'code': 'ZR', 'name': 'Znt Round'})
        cls.art = env['gem.notation.stone'].create({
            'code': 'ZA', 'name': 'Znt Plain',
            'default_shape_id': cls.shape_rd.id,
        })
        cls.art_colour = env['gem.notation.stone'].create({
            'code': 'ZB', 'name': 'Znt Blue Something',
            'implied_hue_id': cls.hue_blue.id,
            'default_shape_id': cls.shape_rd.id,
        })
        cls.service = env['gem.notation']

    def test_build_every_block_combination(self):
        cases = [
            (None, None, None, 'ZA'),
            (self.grade, None, None, 'ZA7'),
            (None, self.hue, None, 'ZA9Z'),
            (self.grade, self.hue, None, 'ZA79Z'),
            (None, None, self.shape, 'ZAZP'),
            (self.grade, None, self.shape, 'ZA7ZP'),
            (None, self.hue, self.shape, 'ZA9ZZP'),
            (self.grade, self.hue, self.shape, 'ZA79ZZP'),
        ]
        for grade, hue, shape, expected in cases:
            built = self.service.build_token(self.art, grade, hue, shape)
            self.assertEqual(built['token'], expected)
            self.assertFalse(built['problems'], expected)

    def test_build_omits_defaults_and_implied(self):
        built = self.service.build_token(self.art, shape=self.shape_rd)
        self.assertEqual(built['token'], 'ZA')
        built = self.service.build_token(self.art_colour, hue=self.hue_blue)
        self.assertEqual(built['token'], 'ZB')
        self.assertFalse(built['problems'])

    def test_build_refuses_double_colour(self):
        built = self.service.build_token(self.art_colour, hue=self.hue)
        self.assertTrue(any('double colour' in p for p in built['problems']))

    def test_parse_round_trip(self):
        for token in ('ZA', 'ZA7', 'ZA9Z', 'ZA79Z', 'ZAZP', 'ZA7ZP',
                      'ZA9ZZP', 'ZA79ZZP'):
            parsed = self.service.parse_token(token)
            self.assertFalse(parsed['problems'], token)
            self.assertEqual(parsed['article'], self.art, token)

    def test_parse_rejects_bad_structures(self):
        for bad in ('Z', 'ZAABC', 'ZA123', 'ZA7Z9'):
            self.assertTrue(self.service.parse_token(bad)['problems'], bad)

    def test_parse_flags_unknowns_and_double_colour(self):
        self.assertIn("unknown article 'XX'",
                      self.service.parse_token('XX7')['problems'][0])
        self.assertTrue(any('double colour' in p for p in
                            self.service.parse_token('ZB9Z')['problems']))

    def test_ordering_and_transcription(self):
        components = [
            {'article': self.art, 'grade': self.grade, 'weight': 2.0},
            {'article': self.art_colour, 'weight': 5.0},
            {'article': self.art, 'hue': self.hue, 'shape': self.shape,
             'weight': 0.5, 'is_center': True},
        ]
        result = self.service.transcribe(components)
        # center first, then heaviest single stone descending
        self.assertEqual(result['code'], 'ZA9ZZP+ZB+ZA7')
        self.assertFalse(result['problems'])

    def test_wizard_compose_mode(self):
        wizard = self.env['gem.notation.wizard'].create({
            'mode': 'compose', 'article_id': self.art.id,
            'grade_id': self.grade.id, 'shape_id': self.shape.id,
        })
        wizard.action_run()
        self.assertIn('Code: ZA7ZP', wizard.result)
        # a default shape is omitted from the code and said so
        wizard.shape_id = self.shape_rd
        wizard.action_run()
        self.assertIn('Code: ZA7\n', wizard.result + '\n')
        self.assertIn('Omitted', wizard.result)

    def test_ui_endpoints_are_json_safe(self):
        boot = self.service.ui_bootstrap()
        self.assertTrue(any(s['code'] == 'ZA' for s in boot['stones']))
        stone_row = next(s for s in boot['stones'] if s['code'] == 'ZB')
        self.assertEqual(stone_row['implied_hue_id'], self.hue_blue.id)
        read = self.service.ui_read('ZA7ZP+ZB9Z')
        self.assertEqual(read['tokens'][0]['stone'], 'Znt Plain')
        self.assertEqual(read['tokens'][0]['grade'], 'Znt Light')
        self.assertEqual(read['tokens'][0]['shape'], 'Znt Pear')
        self.assertTrue(read['tokens'][1]['problems'])  # double colour
        self.assertIn(('ZA', 'Znt Plain'),
                      self.service.ui_read('Znt Plain')['matches']['stones'])

    def test_lookup_both_directions(self):
        found = self.service.lookup('Znt Plain')
        self.assertIn(('ZA', 'Znt Plain'), found['stones'])
        self.assertTrue(self.service.lookup('ZP')['shapes'])
