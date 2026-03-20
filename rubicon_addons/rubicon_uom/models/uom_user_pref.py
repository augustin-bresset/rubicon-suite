from odoo import models, fields


class RubiconUomUserPref(models.Model):
    _name = 'rubicon.uom.user.pref'
    _description = 'Per-user UOM display preference (stub — full implementation in Task 4)'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    category_id = fields.Many2one('rubicon.uom.category', string='Category', required=True, ondelete='cascade')
    uom_id = fields.Many2one('rubicon.uom', string='Unit', required=True, ondelete='cascade')
