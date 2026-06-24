from odoo.tests.common import TransactionCase


class TestSisReferenceP720(TransactionCase):
    """Reference case pinned to the documented SO-EMA-25001 / P720 example.

    From meta/sis/main_with_example.md (Sales Order SO-EMA-25001, single line
    P720-RHO+LAM+GT+PT/P): the frozen inputs are Qty 1, U.Price 195, U.Cost
    118.03; the Items/Profit row and the Profit Details rollup must reproduce
    Amount 195, Cost 118.03, Profit 76.97, Profit % 65.21.

    This is the SIS analog of the R132 reference test: it nails the financial
    rollup to a real documented order rather than synthetic round numbers.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Synthetic client code (ZZQ) so the fixture never collides with seeded
        # SIS data; the documented order this mirrors is SO-EMA-25001.
        cls.doc = cls.env['sis.document'].create({
            'name': 'SO-ZZQ-25001', 'doc_type_code': 'SO',
        })
        cls.item = cls.env['sis.document.item'].create({
            'document_id': cls.doc.id,
            'design': 'P720-RHO+LAM+GT+PT/P',
            'purity': '18K',
            'qty': 1,
            'unit_price': 195.0,
            'unit_cost': 118.03,
        })

    def test_items_profit_row(self):
        # Items/Profit table (main_with_example.md lines 367-375).
        self.assertAlmostEqual(self.item.amount, 195.0, places=2)
        self.assertAlmostEqual(self.item.cost, 118.03, places=2)
        self.assertAlmostEqual(self.item.profit, 76.97, places=2)
        # Profit % 65.21 -> stored fraction 0.6521 (item digits = 6, 4).
        self.assertAlmostEqual(self.item.profit_pct, 0.6521, places=4)

    def test_profit_details_rollup(self):
        # Profit Details panel (main_with_example.md lines 456-469).
        self.assertEqual(self.doc.total_qty, 1)
        self.assertAlmostEqual(self.doc.total_amount, 195.0, places=2)
        self.assertAlmostEqual(self.doc.total_cost, 118.03, places=2)
        self.assertAlmostEqual(self.doc.total_profit, 76.97, places=2)
        # Profit in % 65.21 -> 0.6521; reproducible now that the document field
        # keeps 4 decimals (digits = 6, 4), matching the line.
        self.assertAlmostEqual(self.doc.profit_pct, 0.6521, places=4)
