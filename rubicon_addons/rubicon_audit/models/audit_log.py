from odoo import api, fields, models
from odoo.exceptions import UserError


class RubiconAuditLog(models.Model):
    """Immutable change journal for the sensitive business values.

    Rows are created by rubicon.audit.mixin (with sudo). Managers can read
    them and fill in the `note` (the "why"); nothing else is ever editable
    and rows cannot be deleted, administrators included.
    """
    _name = 'rubicon.audit.log'
    _description = 'Rubicon change history'
    _order = 'id desc'
    _rec_name = 'record_display'

    model_name = fields.Char(required=True, index=True)
    model_label = fields.Char(string='Document')
    res_id = fields.Integer(string='Record ID', required=True, index=True)
    record_display = fields.Char(string='Record')
    operation = fields.Selection(
        [('create', 'Created'), ('write', 'Modified'), ('unlink', 'Deleted')],
        required=True, index=True)
    field_name = fields.Char()
    field_label = fields.Char(string='Field')
    old_value = fields.Char(string='Before')
    new_value = fields.Char(string='After')
    user_id = fields.Many2one('res.users', string='By', required=True, index=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    note = fields.Char(string='Reason', help='Why the value was changed.')

    def write(self, vals):
        if set(vals) - {'note'}:
            raise UserError(self.env._(
                'History entries cannot be modified; only the reason note is editable.'))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _forbid_unlink(self):
        raise UserError(self.env._('History entries cannot be deleted.'))
