from odoo.tests.common import TransactionCase


class TestR132Smoke(TransactionCase):
    """Data smoke test for the R132 reference design (see meta/pdp/smoke_test.md).

    Asserts the structural facts that are stable and config-independent
    (product listing, drawing, metal weight, matching, model labor, stone
    piece counts and recut shapes). Deliberately does NOT assert stone
    weights or costs: those depend on pricing/recutting config that has
    drifted from the original capture and are better covered by a dedicated
    self-contained golden test.

    Skips when the R132 dataset is absent (e.g. a bare test database), so it
    only runs where the reference data is loaded.
    """

    REF_CODE = 'R132-GA+RHO+CT+PF+T/W'
    EXPECTED_PRODUCTS = {
        'R132-GA+RHO+CT+PF+T/W',
        'R132-LAM+RH+PM+PL+D/W',
        'R132-PT+LAM+CT+PM+T/W',
        'R132-RMS+LI+BT+LC+D/W',
    }
    EXPECTED_MATCHING = {'E214', 'P266', 'P867'}
    EXPECTED_LABOR = {'ASS': 242.0, 'CAS': 100.0, 'FIL': 150.0, 'POL': 150.0}
    EXPECTED_STONE_PIECES = {'Citrine': 5, 'Diamond': 27, 'Garnet': 4, 'Rhodolite': 6}

    def setUp(self):
        super().setUp()
        self.ref = self.env['pdp.product'].search([('code', '=', self.REF_CODE)], limit=1)
        if not self.ref:
            self.skipTest("R132 reference data not present in this database")
        self.model = self.ref.model_id

    def test_model_and_drawing(self):
        self.assertEqual(self.model.code, 'R132')
        self.assertEqual(self.model.drawing, 'RP128B')

    def test_model_lists_at_least_the_reference_products(self):
        codes = set(self.env['pdp.product'].search([('model_id', '=', self.model.id)]).mapped('code'))
        self.assertTrue(self.EXPECTED_PRODUCTS.issubset(codes),
                        f"missing products: {self.EXPECTED_PRODUCTS - codes}")

    def test_metal_weight(self):
        metal = self.env['pdp.product.model.metal'].search([
            ('model_id', '=', self.model.id), ('purity_id.code', '=', '18K'),
        ], limit=1)
        self.assertTrue(metal, "no 18K metal weight for R132")
        self.assertEqual(metal.metal_id.code, 'W')           # White Gold
        self.assertAlmostEqual(metal.weight, 8.8, places=2)

    def test_matching_models(self):
        codes = set(self.model.matching_model_ids.mapped('code'))
        self.assertTrue(self.EXPECTED_MATCHING.issubset(codes),
                        f"missing matching models: {self.EXPECTED_MATCHING - codes}")

    def test_model_labor_costs(self):
        lines = self.env['pdp.labor.cost.model'].search([('model_id', '=', self.model.id)])
        by_code = {l.labor_id.code: l for l in lines}
        for code, cost in self.EXPECTED_LABOR.items():
            self.assertIn(code, by_code, f"missing labor {code}")
            self.assertAlmostEqual(by_code[code].cost, cost, places=2)
            self.assertEqual(by_code[code].currency_id.name, 'THB')

    def test_stone_piece_counts(self):
        data = self.ref.get_weight_data()
        pieces = {}
        for row in data['stone_original']:
            pieces[row['type']] = pieces.get(row['type'], 0) + row['pieces']
        for stone_type, count in self.EXPECTED_STONE_PIECES.items():
            self.assertEqual(pieces.get(stone_type), count,
                             f"{stone_type}: expected {count} pieces, got {pieces.get(stone_type)}")

    def test_stones_are_recut_to_bufftop(self):
        # Citrine / Garnet / Rhodolite are recut from Round to Round Bufftop.
        data = self.ref.get_weight_data()
        recut_shapes = {row['type']: row['shape'] for row in data['stone_recut']}
        for stone_type in ('Citrine', 'Garnet', 'Rhodolite'):
            self.assertIn('Bufftop', recut_shapes.get(stone_type, ''),
                          f"{stone_type} should be recut to a Bufftop shape")
