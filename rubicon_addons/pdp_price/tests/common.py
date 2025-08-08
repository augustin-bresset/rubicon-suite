from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo import fields

@tagged('pdp_price', '-at_install', 'post_install')
class PriceCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Currency = cls.env['res.currency']
        # Essaye d'abord les XML IDs standards d'Odoo
        def _ref_or_search(xmlid, name):
            rec = cls.env.ref(xmlid, raise_if_not_found=False)
            if rec:
                return rec
            return cls.Currency.search([('name', '=', name)], limit=1)

        cls.EUR = _ref_or_search('base.EUR', 'EUR')
        cls.THB = _ref_or_search('base.THB', 'THB')
        assert cls.EUR and cls.THB, "Devise(s) manquante(s) EUR/THB"

        cls.Product   = cls.env['pdp.product']
        cls.AddonType = cls.env['pdp.addon.type']
        cls.AddonCost = cls.env['pdp.addon.cost']
        cls.AddonComp = cls.env['pdp.price.addon']
        cls.company   = cls.env.ref('base.main_company')

        # Upsert des taux pour la date du jour de tes computes
        today = fields.Date.to_date('2025-08-08')
        cls._upsert_rate(cls.THB, today, 1.0)       # 1 THB = 1 THB
        cls._upsert_rate(cls.EUR, today, 1.0/40.0)  # 1 EUR = 40 THB

    @classmethod
    def _upsert_rate(cls, currency, date, rate):
        Rate = cls.env['res.currency.rate']
        existing = Rate.search([
            ('currency_id', '=', currency.id),
            ('name', '=', date),
            ('company_id', '=', False),
        ], limit=1)
        if existing:
            existing.rate = rate
        else:
            Rate.create({
                'currency_id': currency.id,
                'name': date,
                'rate': rate,
            })

    # Helpers
    def _product(self, code='TEST-PROD'):
        return self.Product.create({'code': code})
    
    def _addon_type(self, code="AAA", name="TEST-ADDONTYPE"):
        return self.AddonType.create({'code': code, 'name': name})

    def _addon_cost(self, *, product, addon_type, cost, currency):
        return self.AddonCost.create({
            'product_code': product.id,
            'addon_code': addon_type.id,
            'cost': cost,
            'currency': currency.id,
        })

    def _addon_component(self, *, product, currency=None, name='AddonComp'):
        vals = {'name': name, 'product_code': product.id}
        if currency:
            vals['currency'] = currency.id
        return self.AddonComp.create(vals)
