from odoo import models, fields, api


class PdpRole(models.Model):
    """
    Defines roles that group permissions.
    Roles are assigned to users.
    """
    _name = 'pdp.role'
    _description = 'PDP Role'
    _order = 'name'

    name = fields.Char(
        string='Role Name',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Permissions assigned to this role
    permission_ids = fields.Many2many(
        comodel_name='pdp.permission',
        relation='pdp_role_permission_rel',
        column1='role_id',
        column2='permission_id',
        string='Permissions'
    )
    
    # Users assigned to this role
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='pdp_role_user_rel',
        column1='role_id',
        column2='user_id',
        string='Users'
    )

    def has_permission(self, permission_code):
        """
        Check if this role has the given permission.
        """
        self.ensure_one()
        return bool(self.permission_ids.filtered(lambda p: p.code == permission_code))

    @api.model
    def get_user_permissions(self, user=None):
        """
        Returns all permission codes for a user.
        If user is None, uses current user.
        """
        if user is None:
            user = self.env.user
        
        # Get all roles for the user
        roles = self.search([('user_ids', 'in', user.id)])
        
        # Collect all permissions
        permissions = set()
        for role in roles:
            for perm in role.permission_ids:
                permissions.add(perm.code)
        
        return list(permissions)

    @api.model
    def user_has_permission(self, permission_code, user=None):
        """
        Check if a user has a specific permission.
        """
        if user is None:
            user = self.env.user
        
        # Admin bypass
        if user.has_group('base.group_system'):
            return True
        
        permissions = self.get_user_permissions(user)
        return permission_code in permissions


class ResUsers(models.Model):
    """
    Extend res.users to add PDP roles relation.
    """
    _inherit = 'res.users'

    pdp_role_ids = fields.Many2many(
        comodel_name='pdp.role',
        relation='pdp_role_user_rel',
        column1='user_id',
        column2='role_id',
        string='PDP Roles'
    )

    def has_pdp_permission(self, permission_code):
        """
        Check if user has the given PDP permission.
        """
        self.ensure_one()
        return self.env['pdp.role'].user_has_permission(permission_code, self)
