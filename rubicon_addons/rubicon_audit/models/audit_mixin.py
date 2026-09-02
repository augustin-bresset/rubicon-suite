from odoo import api, models


class RubiconAuditMixin(models.AbstractModel):
    """Log create/write/unlink of sensitive fields into rubicon.audit.log.

    Inherit it next to the real model and set `_audit_fields`. Independent of
    the mail stack on purpose (no chatter, no followers, no mail module).
    Set the context key `rubicon_audit_disable` to skip logging (bulk
    migrations); set `_audit_log_create = False` on models whose creations
    are routine and only value changes matter.
    """
    _name = 'rubicon.audit.mixin'
    _description = 'Change-history mixin'

    _audit_fields = ()
    _audit_log_create = True

    def _audit_render(self, field_name):
        """Human-readable value of a field on `self` (one record or empty)."""
        if not self:
            return ''
        value = self[field_name]
        field = self._fields[field_name]
        if field.type == 'many2one':
            return value.display_name or ''
        if field.type == 'selection':
            selection = dict(field.get_description(self.env)['selection'])
            return selection.get(value, value or '')
        if value is False or value is None:
            return ''
        return str(value)

    def _audit_push(self, operation, entries):
        """entries: list of (record, field_name, old, new)."""
        if self.env.context.get('rubicon_audit_disable') or not entries:
            return
        label = self.env['ir.model']._get(self._name).name or self._name
        self.env['rubicon.audit.log'].sudo().create([{
            'model_name': record._name,
            'model_label': label,
            'res_id': record.id,
            'record_display': record.display_name or str(record.id),
            'operation': operation,
            'field_name': field_name or False,
            'field_label': record._fields[field_name].string if field_name else False,
            'old_value': old or False,
            'new_value': new or False,
            'user_id': self.env.uid,
        } for record, field_name, old, new in entries])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self._audit_log_create:
            records._audit_push('create', [(r, None, '', '') for r in records])
        return records

    def write(self, vals):
        tracked = [f for f in self._audit_fields if f in vals]
        before = {r.id: {f: r._audit_render(f) for f in tracked} for r in self} if tracked else {}
        result = super().write(vals)
        entries = []
        for record in self:
            for f in tracked:
                old, new = before[record.id][f], record._audit_render(f)
                if old != new:
                    entries.append((record, f, old, new))
        self._audit_push('write', entries)
        return result

    def unlink(self):
        entries = [(r, None, r.display_name or str(r.id), '') for r in self]
        # Push before the rows disappear; display data is captured above.
        self._audit_push('unlink', entries)
        return super().unlink()
