from odoo.tests.common import TransactionCase


class TestShippedCorrespondence(TransactionCase):
    """The versioned notation<->PDP correspondence must never drift.

    The mapping CSVs in data/ are the contract between the new notation
    and the historical PDP records. These assertions lock them: if a
    regeneration or a curation edit silently changes what a legacy record
    means, this test fails before anything reaches production.
    """

    def test_every_dictionary_entry_is_linked(self):
        self.assertEqual(self.env['gem.notation.stone'].search_count(
            [('type_id', '=', False)]), 0)
        self.assertEqual(self.env['gem.notation.shape'].search_count(
            [('shape_id', '=', False)]), 0)
        self.env.cr.execute("""
            SELECT count(*) FROM pdp_stone_shade sh
            WHERE NOT EXISTS (SELECT 1 FROM gem_notation_shade_map m
                              WHERE m.shade_id = sh.id)""")
        self.assertEqual(self.env.cr.fetchall()[0][0], 0)
        self.env.cr.execute("""
            SELECT count(*) FROM pdp_stone_type t
            WHERE NOT EXISTS (SELECT 1 FROM gem_notation_stone s
                              WHERE s.type_id = t.id)""")
        self.assertEqual(self.env.cr.fetchall()[0][0], 0)

    def test_grade_scales_map_as_decided(self):
        # colour depth A..AAAA -> 1..4, quality judgement 2/3/C -> 5/6/7
        for legacy, digit in [('A', '1'), ('AA', '2'), ('AAA', '3'),
                              ('AAAA', '4'), ('2', '5'), ('3', '6'),
                              ('C', '7')]:
            shade = self.env.ref(f'pdp_stone.shade_{legacy}')
            mapping = self.env['gem.notation.shade.map'].search(
                [('shade_id', '=', shade.id)])
            self.assertEqual(mapping.grade_id.code, digit, legacy)
            self.assertFalse(mapping.hue_id, legacy)

    def test_landmark_mappings(self):
        ref = self.env.ref
        self.assertEqual(ref('gem_notation.stone_SA').type_id,
                         ref('pdp_stone.type_SA'))
        Map = self.env['gem.notation.shade.map']
        grey = Map.search([('shade_id', '=', ref('pdp_stone.shade_GYAAA').id)])
        self.assertEqual(grey.grade_id.code, '3')     # AAA -> Dark
        self.assertEqual(grey.hue_id.name, 'Grey')
        pink_light = Map.search(
            [('shade_id', '=', ref('pdp_stone.shade_PL').id)])
        self.assertEqual(pink_light.grade_id.code, '1')
        self.assertEqual(pink_light.hue_id.name, 'Pink')
        white_sapphire = Map.search(
            [('shade_id', '=', ref('pdp_stone.shade_W_SA').id)])
        self.assertFalse(white_sapphire.grade_id)
        self.assertEqual(white_sapphire.hue_id.name, 'White')

    def test_correspondence_health_check_is_clean(self):
        gaps = self.env['gem.notation'].action_check_correspondence()
        self.assertEqual(gaps, {'types_without_article': 0,
                                'shades_unmapped': 0,
                                'shapes_unlinked': 0})
