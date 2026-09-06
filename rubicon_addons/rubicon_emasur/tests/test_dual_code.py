from odoo.tests.common import TransactionCase


class TestDualNotation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env['pdp.product.model'].create({'code': 'ZZDN1'})
        cls.product = cls.env['pdp.product'].create({
            'code': 'ZZDN1-CIT+GA/W', 'model_id': cls.model.id, 'metal': 'W',
            'active': True})    # name_search skips inactive records by default
        cls.product.alt_code = 'ZZDN1-CT1A+GA/W'

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
        self._set_system('alternative')
        self.assertEqual(self.product.display_name, 'ZZDN1-CT1A+GA/W')
        # No Emasur code on the model yet: it keeps showing its Rubicon code.
        self.assertEqual(self.model.display_name, 'ZZDN1')
        self._set_system('rubicon')
        self.assertEqual(self.product.display_name, 'ZZDN1-CIT+GA/W')

    def test_history_lines_carry_the_converted_design(self):
        doc = self.env['sis.document'].create({'name': 'SO-ZZD-25001', 'doc_type_code': 'SO'})
        item = self.env['sis.document.item'].create({
            'document_id': doc.id, 'design': 'ZZDN1-CIT+GA/W', 'sequence': 1})
        self.assertEqual(item.alt_design, 'ZZDN1-CT1A+GA/W')
        hits = self.env['sis.document.item'].search(
            [('alt_design', 'ilike', 'CT1A')])
        self.assertIn(item, hits)
        # A design with an unmapped token stores nothing rather than half a translation
        item.write({'design': 'ZZDN1-XXX9/W'})
        self.assertFalse(item.alt_design)

    def test_backfill_is_setwise_and_rerunnable(self):
        doc = self.env['sis.document'].create({'name': 'SO-ZZD-25002', 'doc_type_code': 'SO'})
        ok = self.env['sis.document.item'].create({
            'document_id': doc.id, 'design': 'ZZDN1-GA+PER/Y', 'sequence': 1})
        ko = self.env['sis.document.item'].create({
            'document_id': doc.id, 'design': 'ZZDN1-XXX9/Y', 'sequence': 2})
        filled, distinct, total = self.env['sis.document.item'].action_backfill_alt_design()
        self.assertGreaterEqual(filled, 1)
        self.assertGreaterEqual(total, 2)
        self.assertEqual(ok.alt_design, 'ZZDN1-GA+PER/Y')
        self.assertFalse(ko.alt_design)

    def test_wizard_switches_the_parameter(self):
        wizard = self.env['emasur.system.wizard'].create({'system': 'alternative'})
        wizard.action_apply()
        self.assertEqual(self.env['emasur.code.mixin'].emasur_active_system(), 'alternative')


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
        cls.model.alt_code = 'NR-R900'
        cls.ring_a.alt_code = 'NR-R900.1'
        cls.ring_b.alt_code = 'NR-R900.2'

    def _set_system(self, system):
        self.env['ir.config_parameter'].sudo().set_param('rubicon_notation.system', system)
        self.env.invalidate_all()

    def test_search_hits_old_and_new_regardless_of_the_active_system(self):
        Product = self.env['pdp.product']
        for system in ('rubicon', 'alternative'):
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
        self._set_system('alternative')
        self.assertEqual(self.ring_a.display_name, 'NR-R900.1')
        self.assertEqual(self.model.display_name, 'NR-R900')
        self.assertEqual(orphan.display_name, 'ZZR900-PER/Y')
        self._set_system('rubicon')
        self.assertEqual(self.ring_a.display_name, 'ZZR900-CIT+GA/W')

    def test_wizard_offers_every_registered_system(self):
        wizard = self.env['emasur.convert.wizard']  # unrelated model untouched
        selection = self.env['emasur.system.wizard']._system_selection()
        self.assertEqual([key for key, _label in selection], ['rubicon', 'alternative'])

    def test_unknown_system_parameter_falls_back_to_rubicon(self):
        self._set_system('martian')
        self.assertEqual(self.env['emasur.code.mixin'].emasur_active_system(), 'rubicon')
        self.assertEqual(self.ring_a.display_name, 'ZZR900-CIT+GA/W')


class TestAlternativeCodeProvenance(TransactionCase):
    """One alternative code, its source telling assigned from computed:
    composed codes are derived by the converter, official ones are loaded
    and never overwritten by a recompute."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env['pdp.product.model'].create({'code': 'ZZPC9'})
        cls.product = cls.env['pdp.product'].create({
            'code': 'ZZPC9-CIT+GA/W', 'model_id': cls.model.id,
            'metal': 'W', 'active': True})

    def test_composed_code_is_computed_on_create_and_searchable(self):
        self.assertEqual(self.product.alt_code, 'ZZPC9-CT1A+GA/W')
        self.assertEqual(self.product.alt_code_source, 'computed')
        hits = [rid for rid, _n in self.env['pdp.product'].name_search('ZZPC9-CT1A')]
        self.assertIn(self.product.id, hits)

    def test_manual_or_imported_code_is_official_and_protected(self):
        self.product.write({'alt_code': 'NEW-OFFICIAL-1'})
        self.assertEqual(self.product.alt_code_source, 'official')
        self.product.write({'code': 'ZZPC9-GA/W'})       # recompute triggered...
        self.assertEqual(self.product.alt_code, 'NEW-OFFICIAL-1')  # ...but protected
        filled, total = self.env['pdp.product'].action_recompute_alt_codes()
        self.assertEqual(self.product.alt_code, 'NEW-OFFICIAL-1')

    def test_incomplete_conversion_clears_the_computed_code(self):
        self.product.write({'code': 'ZZPC9-XXX9/W'})
        self.assertFalse(self.product.alt_code)
        self.assertFalse(self.product.alt_code_source)

    def test_display_shows_the_computed_code_internally(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'rubicon_notation.system', 'alternative')
        self.env.invalidate_all()
        self.assertEqual(self.product.display_name, 'ZZPC9-CT1A+GA/W')

    def test_setwise_recompute_counts_and_respects_official(self):
        other = self.env['pdp.product'].create({
            'code': 'ZZPC9-GA+PER/Y', 'model_id': self.model.id,
            'metal': 'Y', 'active': True})
        self.product.write({'alt_code': 'NEW-OFFICIAL-2'})
        filled, total = self.env['pdp.product'].action_recompute_alt_codes()
        self.assertGreaterEqual(total, 2)
        self.assertEqual(other.alt_code, 'ZZPC9-GA+PER/Y')
        self.assertEqual(other.alt_code_source, 'computed')
        self.assertEqual(self.product.alt_code, 'NEW-OFFICIAL-2')


class TestUserNotationPreference(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'notation user', 'login': 'notation_user',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.Mixin = cls.env['emasur.code.mixin']

    def test_user_preference_overrides_the_company_default(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'rubicon_notation.system', 'rubicon')
        as_user = self.Mixin.with_user(self.user)
        self.assertEqual(as_user.emasur_active_system(), 'rubicon')
        as_user.set_user_notation('alternative')     # a plain user sets their own
        self.assertEqual(as_user.emasur_active_system(), 'alternative')
        self.assertEqual(self.Mixin.emasur_active_system(), 'rubicon')  # others untouched
        as_user.set_user_notation(False)             # back to the company default
        self.assertEqual(as_user.emasur_active_system(), 'rubicon')

    def test_ui_payload_and_invalid_values(self):
        ui = self.Mixin.get_notation_ui()
        self.assertEqual([k for k, _l in ui['systems']], ['rubicon', 'alternative'])
        self.assertIn(ui['active'], ('rubicon', 'alternative'))
        as_user = self.Mixin.with_user(self.user)
        self.assertEqual(as_user.set_user_notation('martian'), 'rubicon')
