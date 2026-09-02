from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestAuditLog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.Log = env['rubicon.audit.log']
        cls.usd = env.ref('base.USD')
        cls.stone_type = env['pdp.stone.type'].create({'code': 'ZZAU', 'name': 'Audit type'})
        cls.stone_size = env['pdp.stone.size'].create({'name': 'ZZ9X9'})
        cls.stone = env['pdp.stone'].create({
            'code': 'ZZAU-9X9', 'type_id': cls.stone_type.id,
            'size_id': cls.stone_size.id, 'cost': 10.0,
            'currency_id': cls.usd.id,
        })
        Users = env['res.users'].with_context(no_reset_password=True)
        cls.manager = Users.create({
            'name': 'audit manager', 'login': 'audit_manager',
            'groups_id': [(6, 0, [env.ref('base.group_user').id,
                                  env.ref('rubicon_env.group_rubicon_manager').id])],
        })
        cls.reader = Users.create({
            'name': 'audit reader', 'login': 'audit_reader',
            'groups_id': [(6, 0, [env.ref('base.group_user').id])],
        })

    def _logs(self, record):
        return self.Log.search([('model_name', '=', record._name),
                                ('res_id', '=', record.id)])

    def test_write_is_journaled_with_old_and_new(self):
        self.stone.with_user(self.manager).write({'cost': 12.5})
        log = self._logs(self.stone).filtered(lambda l: l.operation == 'write')
        self.assertEqual(len(log), 1)
        self.assertEqual(log.field_name, 'cost')
        self.assertEqual((log.old_value, log.new_value), ('10.0', '12.5'))
        self.assertEqual(log.user_id, self.manager)
        self.assertEqual(log.record_display, 'ZZAU-9X9')

    def test_many2one_rendered_with_display_name(self):
        eur = self.env.ref('base.EUR')
        self.stone.write({'currency_id': eur.id})
        log = self._logs(self.stone).filtered(lambda l: l.field_name == 'currency_id')
        self.assertEqual((log.old_value, log.new_value), ('USD', 'EUR'))

    def test_untracked_field_and_equal_value_produce_no_row(self):
        count = len(self._logs(self.stone))
        self.stone.write({'weight': 1.23})     # not an audited field
        self.stone.write({'cost': 10.0})       # unchanged value
        self.assertEqual(len(self._logs(self.stone)), count)

    def test_create_and_unlink_are_journaled(self):
        margin = self.env['pdp.margin'].create({'code': 'ZZAU', 'name': 'Audit margin'})
        self.assertEqual(self._logs(margin).mapped('operation'), ['create'])
        logs_model, logs_id = margin._name, margin.id
        margin.unlink()
        operations = self.Log.search([('model_name', '=', logs_model),
                                      ('res_id', '=', logs_id)]).mapped('operation')
        self.assertCountEqual(operations, ['create', 'unlink'])

    def test_item_creation_not_journaled(self):
        doc = self.env['sis.document'].create({'name': 'SO-ZZA-25001', 'doc_type_code': 'SO'})
        item = self.env['sis.document.item'].create({
            'document_id': doc.id, 'design': 'ZZAU-TEST', 'sequence': 1})
        self.assertFalse(self._logs(item))
        item.write({'unit_price': 99.0})
        self.assertEqual(self._logs(item).field_name, 'unit_price')

    def test_context_flag_disables_journal(self):
        count = len(self._logs(self.stone))
        self.stone.with_context(rubicon_audit_disable=True).write({'cost': 77.0})
        self.assertEqual(len(self._logs(self.stone)), count)

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.addons.base.models.ir_rule')
    def test_journal_is_immutable_and_manager_only(self):
        self.stone.write({'cost': 20.0})
        log = self._logs(self.stone).filtered(lambda l: l.operation == 'write')[:1]
        log.with_user(self.manager).write({'note': 'yearly price revision'})
        self.assertEqual(log.note, 'yearly price revision')
        with self.assertRaises(UserError):
            log.with_user(self.manager).write({'new_value': '9999'})
        with self.assertRaises(UserError):
            log.unlink()
        with self.assertRaises(AccessError):
            self.Log.with_user(self.reader).search([])
