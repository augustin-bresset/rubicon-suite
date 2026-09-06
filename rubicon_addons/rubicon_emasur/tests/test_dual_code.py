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


class TestSwitchDressRehearsal(TransactionCase):
    """Day-one dress rehearsal with an invented code system.

    Plays the whole switch on synthetic codes (no Emasur data involved):
    load alternative codes, search by both systems, flip the display, keep
    the history searchable — proving the machinery does not depend on what
    the real delivered codes will look like.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.model = env['pdp.product.model'].create({'code': 'ZZR900'})
        cls.ring_a = env['pdp.product'].create({
            'code': 'ZZR900-CIT+GA/W', 'model_id': cls.model.id,
            'metal': 'W', 'active': True})
        cls.ring_b = env['pdp.product'].create({
            'code': 'ZZR900-GA/P', 'model_id': cls.model.id,
            'metal': 'P', 'active': True})
        # The invented system: model codes gain a series prefix, product
        # codes are rebuilt on the model's new code ("pas radical").
        cls.model.emasur_code = 'NR-R900'
        cls.ring_a.emasur_code = 'NR-R900.1'
        cls.ring_b.emasur_code = 'NR-R900.2'

    def _set_system(self, system):
        self.env['ir.config_parameter'].sudo().set_param('rubicon_notation.system', system)
        self.env.invalidate_all()

    def test_search_hits_old_and_new_regardless_of_the_active_system(self):
        Product = self.env['pdp.product']
        for system in ('rubicon', 'emasur'):
            self._set_system(system)
            for term, expected in [('ZZR900-CIT', self.ring_a),
                                   ('NR-R900.1', self.ring_a),
                                   ('NR-R900.2', self.ring_b)]:
                hits = [rid for rid, _n in Product.name_search(term)]
                self.assertIn(expected.id, hits, (system, term))
        hits = [rid for rid, _n in self.env['pdp.product.model'].name_search('NR-R900')]
        self.assertIn(self.model.id, hits)

    def test_display_flips_and_falls_back(self):
        orphan = self.env['pdp.product'].create({
            'code': 'ZZR900-PER/Y', 'model_id': self.model.id,
            'metal': 'Y', 'active': True})   # no new code loaded yet
        self._set_system('emasur')
        self.assertEqual(self.ring_a.display_name, 'NR-R900.1')
        self.assertEqual(self.model.display_name, 'NR-R900')
        self.assertEqual(orphan.display_name, 'ZZR900-PER/Y')
        self._set_system('rubicon')
        self.assertEqual(self.ring_a.display_name, 'ZZR900-CIT+GA/W')

    def test_wizard_offers_every_registered_system(self):
        wizard = self.env['emasur.convert.wizard']  # unrelated model untouched
        selection = self.env['emasur.system.wizard']._system_selection()
        self.assertEqual([key for key, _label in selection], ['rubicon', 'emasur'])

    def test_unknown_system_parameter_falls_back_to_rubicon(self):
        self._set_system('martian')
        self.assertEqual(self.env['emasur.code.mixin'].emasur_active_system(), 'rubicon')
        self.assertEqual(self.ring_a.display_name, 'ZZR900-CIT+GA/W')
