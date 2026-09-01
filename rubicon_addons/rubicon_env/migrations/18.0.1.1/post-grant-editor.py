"""Access levels introduced in 18.0.1.1.

Before this version every internal user had full access to every Rubicon
model. Now "Internal User" only implies read access (Rubicon / User); writing
requires Rubicon / Editor. So that the upgrade does not lock anyone out of
their daily work, every existing active internal user is granted Editor here.
Administrators (Settings) are Managers through base.group_system. Narrow the
rights afterwards from Settings > Users, by assigning roles.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    editor = env.ref('rubicon_env.group_rubicon_editor', raise_if_not_found=False)
    if not editor:
        return
    users = env['res.users'].search([
        ('share', '=', False), ('active', '=', True), ('id', '!=', SUPERUSER_ID),
    ])
    editor.write({'users': [(4, user.id) for user in users]})
