# pdp_price/tests/test_smoke.py
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestSmoke(TransactionCase):
    def test_smoke(self):
        self.assertTrue(True)
