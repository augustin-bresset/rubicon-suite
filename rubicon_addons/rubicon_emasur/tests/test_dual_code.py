from odoo.tests.common import TransactionCase


class TestDualNotation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env['pdp.product.model'].create({'code': 'ZZDN1'})
        cls.product = cls.env['pdp.product'].create({
            'code': 'ZZDN1-CIT+GA/W', 'model_id': cls.model.id, 'metal': 'W',
            'active': True})    # name_search skips inactive records by default
        cls.product.emasur_code = 'ZZDN1-CT1A+GA/W'

    def _set_system(self, system):
        self.env['ir.config_parameter'].sudo().set_param('rubicon_notation.system', system)
        self.env.invalidate_all()

    def test_name_search_finds_both_codes(self):
        Product = self.env['pdp.product']
        for term in ('ZZDN1-CIT', 'ZZDN1-CT1A'):
            hits = [record_id for record_id, _name in Product.name_search(term)]
            self.assertIn(self.product.id, hits, term)

    def test_display_follows_the_active_system_with_fallback(self):
        self.assertEqual(self.product.display_name, 'ZZDN1-CIT+GA/W')
        self._set_system('emasur')
        self.assertEqual(self.product.display_name, 'ZZDN1-CT1A+GA/W')
        # No Emasur code on the model yet: it keeps showing its Rubicon code.
        self.assertEqual(self.model.display_name, 'ZZDN1')
        self._set_system('rubicon')
        self.assertEqual(self.product.display_name, 'ZZDN1-CIT+GA/W')

    def test_history_lines_carry_the_converted_design(self):
        doc = self.env['sis.document'].create({'name': 'SO-ZZD-25001', 'doc_type_code': 'SO'})
        item = self.env['sis.document.item'].create({
            'document_id': doc.id, 'design': 'ZZDN1-CIT+GA/W', 'sequence': 1})
        self.assertEqual(item.design_emasur, 'ZZDN1-CT1A+GA/W')
        hits = self.env['sis.document.item'].search(
            [('design_emasur', 'ilike', 'CT1A')])
        self.assertIn(item, hits)
        # A design with an unmapped token stores nothing rather than half a translation
        item.write({'design': 'ZZDN1-XXX9/W'})
        self.assertFalse(item.design_emasur)

    def test_backfill_is_setwise_and_rerunnable(self):
        doc = self.env['sis.document'].create({'name': 'SO-ZZD-25002', 'doc_type_code': 'SO'})
        ok = self.env['sis.document.item'].create({
            'document_id': doc.id, 'design': 'ZZDN1-GA+PER/Y', 'sequence': 1})
        ko = self.env['sis.document.item'].create({
            'document_id': doc.id, 'design': 'ZZDN1-XXX9/Y', 'sequence': 2})
        filled, distinct, total = self.env['sis.document.item'].action_backfill_design_emasur()
        self.assertGreaterEqual(filled, 1)
        self.assertGreaterEqual(total, 2)
        self.assertEqual(ok.design_emasur, 'ZZDN1-GA+PER/Y')
        self.assertFalse(ko.design_emasur)

    def test_wizard_switches_the_parameter(self):
        wizard = self.env['emasur.system.wizard'].create({'system': 'emasur'})
        wizard.action_apply()
        self.assertEqual(self.env['emasur.code.mixin'].emasur_active_system(), 'emasur')
