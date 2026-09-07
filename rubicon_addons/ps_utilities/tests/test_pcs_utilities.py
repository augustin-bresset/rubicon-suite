from odoo.tests.common import TransactionCase


class TestPcsUtilities(TransactionCase):
    """The PCS Utilities master-data models support plain CRUD and their links."""

    # Fixture codes are ZZ-prefixed: real master data (simulator, imports)
    # already uses the natural codes (CUT, SET, STN...) and codes are unique.

    def test_role_user_link(self):
        role = self.env['pcs.role'].create({'code': 'ZZSET', 'name': 'Setter'})
        user = self.env['pcs.user'].create({
            'code': 'ZZALC', 'name': 'Alice', 'role_id': role.id})
        self.assertEqual(user.role_id, role)
        self.assertTrue(user.active)

    def test_department_group_and_flags(self):
        grp = self.env['pcs.dept.group'].create({
            'code': 'ZZSTN', 'name': 'Stones', 'sequence': 5})
        dept = self.env['pcs.department'].create({
            'code': 'ZZCUT', 'name': 'Cutting', 'group_id': grp.id,
            'loss_pct': 2.5, 'stones': True})
        self.assertEqual(dept.group_id, grp)
        self.assertTrue(dept.stones)
        self.assertFalse(dept.metals)
        self.assertIn(dept, grp.department_ids)

    def test_employee_type_and_departments(self):
        etype = self.env['pcs.employee.type'].create({'code': 'ZZINH', 'name': 'In House'})
        dept = self.env['pcs.department'].create({'code': 'ZZCT2', 'name': 'Cutting'})
        emp = self.env['pcs.employee'].create({
            'code': 'B01', 'name': 'Bob', 'type_id': etype.id, 'tag': 'T1',
            'department_ids': [(6, 0, [dept.id])]})
        self.assertEqual(emp.type_id, etype)
        self.assertIn(dept, emp.department_ids)

    def test_ssp_seed_data_loaded(self):
        codes = self.env['pcs.ssp'].search([]).mapped('code')
        self.assertIn('PLT', codes)
        self.assertIn('SLD', codes)
        self.assertIn('SPG', codes)
