"""The three Rubicon access levels, checked on a PDP model.

Internal users read; Editors create and write; Managers also delete. Roles
imply a level. Defined in rubicon_env/security/security.xml and applied by
every module's ir.model.access.csv.
"""
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestAccessLevels(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        internal = cls.env.ref('base.group_user')

        def make_user(login, *groups):
            return Users.create({
                'name': login, 'login': login,
                'groups_id': [(6, 0, [internal.id] + [g.id for g in groups])],
            })

        cls.reader = make_user('access_reader')
        cls.editor = make_user('access_editor', cls.env.ref('rubicon_env.group_rubicon_editor'))
        cls.manager = make_user('access_manager', cls.env.ref('rubicon_env.group_rubicon_manager'))
        cls.category = cls.env['pdp.product.category'].create({'code': 'TAC', 'name': 'Access test', 'waste': 0.0})

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.addons.base.models.ir_rule')
    def test_internal_user_reads_only(self):
        Category = self.env['pdp.product.category'].with_user(self.reader)
        self.assertEqual(Category.browse(self.category.id).name, 'Access test')
        with self.assertRaises(AccessError):
            Category.create({'code': 'TAX', 'name': 'not allowed', 'waste': 0.0})
        with self.assertRaises(AccessError):
            self.category.with_user(self.reader).write({'name': 'not allowed'})
        with self.assertRaises(AccessError):
            self.category.with_user(self.reader).unlink()

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.addons.base.models.ir_rule')
    def test_editor_writes_but_cannot_delete(self):
        Category = self.env['pdp.product.category'].with_user(self.editor)
        record = Category.create({'code': 'TAE', 'name': 'editor', 'waste': 0.0})
        record.write({'name': 'editor, renamed'})
        self.assertEqual(record.name, 'editor, renamed')
        with self.assertRaises(AccessError):
            record.unlink()

    def test_manager_deletes(self):
        record = self.env['pdp.product.category'].with_user(self.manager).create({'code': 'TAM', 'name': 'manager', 'waste': 0.0})
        record.unlink()
        self.assertFalse(record.exists())

    def test_levels_are_nested_and_roles_imply_them(self):
        ref = self.env.ref
        self.assertIn(ref('rubicon_env.group_rubicon_user'), ref('base.group_user').implied_ids)
        self.assertIn(ref('rubicon_env.group_rubicon_user'), ref('rubicon_env.group_rubicon_editor').implied_ids)
        self.assertIn(ref('rubicon_env.group_rubicon_editor'), ref('rubicon_env.group_rubicon_manager').implied_ids)
        self.assertIn(ref('rubicon_env.group_rubicon_manager'), ref('base.group_system').implied_ids)
        self.assertIn(ref('rubicon_env.group_rubicon_editor'), ref('rubicon_env.group_rubicon_officer').implied_ids)
        self.assertIn(ref('rubicon_env.group_rubicon_manager'), ref('rubicon_env.group_rubicon_director').implied_ids)
        self.assertIn(ref('rubicon_env.group_rubicon_user'), ref('rubicon_env.group_rubicon_accountant').implied_ids)
        # Administrators end up Managers through the implication chain
        self.assertTrue(self.env.ref('base.user_admin').has_group('rubicon_env.group_rubicon_manager'))
