from odoo.tests.common import TransactionCase


class TestSisFinancialRollup(TransactionCase):
    """Line amounts and document totals derive from the frozen unit price/cost.

    unit_price / unit_cost are the frozen inputs (set when the line is priced);
    amount / cost / profit and the document totals are computed from them, so
    they always stay consistent with the items (and follow an edit).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.doc = cls.env['sis.document'].create({'name': 'SQ-TEST-1', 'doc_type_code': 'SQ'})
        Item = cls.env['sis.document.item']
        cls.item1 = Item.create({
            'document_id': cls.doc.id, 'sequence': 10,
            'qty': 2, 'unit_price': 100.0, 'unit_cost': 60.0,
        })
        cls.item2 = Item.create({
            'document_id': cls.doc.id, 'sequence': 20,
            'qty': 3, 'unit_price': 50.0, 'unit_cost': 40.0,
        })

    def test_item_amounts_computed(self):
        # item1: amount 2*100=200, cost 2*60=120, profit 80, profit% 80/120
        self.assertAlmostEqual(self.item1.amount, 200.0, places=2)
        self.assertAlmostEqual(self.item1.cost, 120.0, places=2)
        self.assertAlmostEqual(self.item1.profit, 80.0, places=2)
        self.assertAlmostEqual(self.item1.profit_pct, 80.0 / 120.0, places=4)

    def test_document_totals_roll_up(self):
        # totals = sum of items: amount 350, cost 240, profit 110, qty 5
        self.assertEqual(self.doc.total_qty, 5)
        self.assertAlmostEqual(self.doc.total_amount, 350.0, places=2)
        self.assertAlmostEqual(self.doc.total_cost, 240.0, places=2)
        self.assertAlmostEqual(self.doc.total_profit, 110.0, places=2)
        # document profit_pct stores 4 decimals (digits=(6, 4)), matching the line
        self.assertAlmostEqual(self.doc.profit_pct, 110.0 / 240.0, places=4)

    def test_totals_follow_an_edit(self):
        # Editing a line's qty re-rolls the line and the document totals.
        self.item1.qty = 4
        self.assertAlmostEqual(self.item1.amount, 400.0, places=2)
        self.assertAlmostEqual(self.doc.total_amount, 550.0, places=2)  # 400 + 150
        self.assertAlmostEqual(self.doc.total_cost, 360.0, places=2)    # 240 + 120
        self.assertAlmostEqual(self.doc.total_profit, 190.0, places=2)  # 160 + 30

    def test_removing_a_line_updates_totals(self):
        self.item2.unlink()
        self.assertAlmostEqual(self.doc.total_amount, 200.0, places=2)
        self.assertEqual(self.doc.total_qty, 2)
