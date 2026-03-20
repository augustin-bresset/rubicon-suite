from odoo import models, fields


class RubiconUomCategory(models.Model):
    _name = 'rubicon.uom.category'
    _description = 'UOM Category (dimension)'
    _rec_name = 'code'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, index=True)
    description = fields.Char(string='Description')
    # Declared here so views and get_user_uom() can reference it without _inherit tricks.
    # The inverse side (rubicon.uom.category_id) is defined in uom.py.
    uom_ids = fields.One2many('rubicon.uom', 'category_id', string='Units')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Category code must be unique.'),
    ]

    def get_user_uom(self, user_id=None):
        """Return the active display unit for a given user.

        Fallback chain: user pref → global default → reference unit.
        Never returns False — reference unit is always present.
        """
        self.ensure_one()
        uid = user_id or self.env.uid
        pref = self.env['rubicon.uom.user.pref'].search([
            ('user_id', '=', uid),
            ('category_id', '=', self.id),
        ], limit=1)
        if pref:
            return pref.uom_id

        default = self.env['rubicon.uom'].search([
            ('category_id', '=', self.id),
            ('is_global_default', '=', True),
        ], limit=1)
        if default:
            return default

        return self.env['rubicon.uom'].search([
            ('category_id', '=', self.id),
            ('is_reference', '=', True),
        ], limit=1)
