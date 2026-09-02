from odoo.tests.common import TransactionCase


class TestEmasurConverter(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.convert = cls.env['emasur.converter']
        ref = cls.env.ref
        cls.agate = ref('pdp_stone.type_AGA')
        cls.white = ref('pdp_stone.shade_WH')
        cls.shape_baf = ref('pdp_stone.shape_BAF')     # Ball Facetted -> BEAD + FACE
        cls.size = cls.env['pdp.stone.size'].create({'name': 'ZZ10X8'})
        cls.stone = cls.env['pdp.stone'].create({
            'code': 'ZZAGAWH-BAF-10X8', 'type_id': cls.agate.id,
            'shade_id': cls.white.id, 'shape_id': cls.shape_baf.id,
            'size_id': cls.size.id, 'cost': 5.0,
            'currency_id': cls.env.ref('base.USD').id,
        })

    def test_data_prematching_holds(self):
        """Spot-check the generated mapping data the converter relies on."""
        ref = self.env.ref
        self.assertEqual(ref('rubicon_emasur.stone_W_AG').type_id.code, 'AGA')
        self.assertEqual(ref('rubicon_emasur.stone_W_AG').shade_id.code, 'WH')
        self.assertEqual(ref('rubicon_emasur.stone_CT1A').type_id.code, 'CIT')
        self.assertEqual(ref('rubicon_emasur.stone_RHO').type_id.code, 'RHO')
        self.assertFalse(ref('rubicon_emasur.stone_RHO').shade_id)
        m = self.env['emasur.shape.map'].search(
            [('rubicon_shape_id', '=', self.shape_baf.id)])
        self.assertEqual((m.shape_id.code, m.cut_id.code), ('BEAD', 'FACE'))

    def test_stone_to_emasur(self):
        out = self.convert.stone_to_emasur(self.stone)
        self.assertEqual(out['stone_code'], 'W.AG')
        self.assertEqual(out['shape_code'], 'BEAD')
        self.assertEqual(out['cut_code'], 'FACE')
        self.assertEqual(out['size'], 'ZZ10X8')
        self.assertTrue(out['exact'])
        # By code string too
        self.assertEqual(
            self.convert.stone_to_emasur('ZZAGAWH-BAF-10X8')['stone_code'], 'W.AG')

    def test_stone_to_emasur_falls_back_to_species(self):
        teal = self.env.ref('pdp_stone.shade_TL')      # no Teal Agate at Emasur
        stone = self.env['pdp.stone'].create({
            'code': 'ZZAGATL-BAF-10X8', 'type_id': self.agate.id,
            'shade_id': teal.id, 'shape_id': self.shape_baf.id,
            'size_id': self.size.id, 'cost': 5.0,
            'currency_id': self.env.ref('base.USD').id,
        })
        out = self.convert.stone_to_emasur(stone)
        self.assertEqual(out['stone_code'], 'AG')
        self.assertFalse(out['exact'])

    def test_stone_from_emasur(self):
        out = self.convert.stone_from_emasur('W.AG', shape_code='BEAD',
                                             cut_code='FACE', size='ZZ10X8')
        self.assertEqual(out['type_code'], 'AGA')
        self.assertEqual(out['shade_code'], 'WH')
        self.assertIn('ZZAGAWH-BAF-10X8', out['candidate_stones'])
        self.assertIn('error', self.convert.stone_from_emasur('NOPE'))

    def test_design_round_trip(self):
        out = self.convert.design_to_emasur('ZZM1-CIT+GA/W')
        self.assertEqual(out['code'], 'ZZM1-CT1A+GA/W')
        self.assertFalse(out['unknown'])
        back = self.convert.design_from_emasur(out['code'])
        self.assertEqual(back['code'], 'ZZM1-CIT+GA/W')

    def test_legacy_aliases_and_fallbacks(self):
        convert = self.convert
        self.assertEqual(convert.token_to_emasur('TT'), 'TTLB')     # alias to (DTS, T2)
        self.assertEqual(convert.token_to_emasur('DT'), 'DTS')
        self.assertEqual(convert.token_to_emasur('GQ'), 'GQ')       # colour word is the species
        self.assertEqual(convert.token_to_emasur('GA'), 'GA')       # shortest code wins over CA.GA
        self.assertEqual(convert.token_to_emasur('BTA'), 'BTA')     # BT+A -> generic Blue Topaz
        self.assertEqual(convert.token_to_emasur('ONYX'), 'ONYX')

    def test_design_with_legacy_compound_and_unknown_tokens(self):
        # AGAWH is a legacy TYPE+SHADE compound; XXX9 maps to nothing.
        out = self.convert.design_to_emasur('ZZM1-AGAWH+XXX9/P')
        self.assertEqual(out['code'], 'ZZM1-W.AG+?XXX9?/P')
        self.assertEqual(out['unknown'], ['XXX9'])

    def test_wizard(self):
        wizard = self.env['emasur.convert.wizard'].create({
            'direction': 'to_emasur', 'kind': 'design',
            'input_code': 'ZZM1-CIT+GA/W',
        })
        wizard.action_convert()
        self.assertEqual(wizard.result, 'ZZM1-CT1A+GA/W')
