# pdp_price/tests/test_price_addon.py

from odoo.tests import tagged
from odoo import fields
from .common import PriceCommon

@tagged('pdp_price', '-at_install', 'post_install')
class TestPriceAddon(PriceCommon):

    def test_cost_sum_converted(self):
        """
        Somme des pdp.addon.cost du produit, convertie vers la devise du composant.
        Hypothèse fixture: 1 EUR = 40 THB, today = 2025-08-08.
        """
        product = self._product()
        addon_type = self._addon_type()
        # 10 EUR + 100 THB
        self._addon_cost(product=product, addon_type=addon_type, cost=10.0, currency=self.EUR)
        self._addon_cost(product=product, addon_type=addon_type, cost=100.0, currency=self.THB)

        comp_thb = self._addon_component(product=product, currency=self.THB, name='THB Comp')
        comp_thb.flush_recordset()
        # 10 EUR -> 400 THB; + 100 THB = 500 THB
        assert round(comp_thb.cost, 4) == 500.0

        # En EUR maintenant
        comp_thb.write({'currency': self.EUR.id})
        comp_thb.flush_recordset()
        # 100 THB -> 2.5 EUR; + 10 EUR = 12.5 EUR
        assert round(comp_thb.cost, 4) == 12.5

    def test_default_currency_is_company(self):
        """Si currency est omise sur le composant, on prend celle de la société (THB)."""
        product = self._product()
        addon_type = self._addon_type()
        self._addon_cost(product=product, addon_type=addon_type, cost=40.0, currency=self.EUR)  # = 1600 THB
        comp = self._addon_component(product=product, name='Default curr')
        comp.flush_recordset()
        assert comp.currency.id == self.company.currency_id.id
        assert round(comp.cost, 4) == 1600.0

    def test_recompute_on_currency_change(self):
        """Le recompute se fait quand on touche product/currency (on teste currency)."""
        product = self._product()
        addon_type = self._addon_type()
        self._addon_cost(product=product, addon_type=addon_type, cost=10.0, currency=self.EUR)   # 400 THB
        comp = self._addon_component(product=product, currency=self.THB)
        comp.flush_recordset()
        assert round(comp.cost, 4) == 400.0

        # Ajout d’un nouveau coût (THB) puis on force un write sur currency pour déclencher le compute
        self._addon_cost(product=product, addon_type=addon_type, cost=60.0, currency=self.THB)   # +60 THB
        comp.write({'currency': self.THB.id})
        comp.flush_recordset()
        assert round(comp.cost, 4) == 460.0

    def test_price_equals_cost_plus_margin(self):
        """
        price = cost + margin.
        Comme _compute_margin n’est pas encore implémenté, on pose margin manuellement.
        """
        product = self._product()
        addon_type = self._addon_type()
        self._addon_cost(product=product, addon_type=addon_type, cost=100.0, currency=self.THB)
        comp = self._addon_component(product=product, currency=self.THB)
        comp.flush_recordset()
        assert round(comp.cost, 4) == 100.0

        comp.write({'margin': 25.0})
        comp.flush_recordset()
        assert round(comp.price, 4) == 125.0
