from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RubiconUomUserPref(models.Model):
    _name = 'rubicon.uom.user.pref'
    _description = 'Per-user UOM display preference'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    category_id = fields.Many2one(
        'rubicon.uom.category', string='Category', required=True, ondelete='cascade',
    )
    uom_id = fields.Many2one('rubicon.uom', string='Unit', required=True, ondelete='cascade')

    _sql_constraints = [
        ('unique_user_category', 'UNIQUE(user_id, category_id)',
         'A user can only have one UOM preference per category.'),
    ]

    @api.constrains('uom_id', 'category_id')
    def _check_uom_matches_category(self):
        for rec in self:
            if rec.uom_id.category_id != rec.category_id:
                raise ValidationError(
                    _('Unit "%s" does not belong to category "%s".')
                    % (rec.uom_id.symbol, rec.category_id.code)
                )
