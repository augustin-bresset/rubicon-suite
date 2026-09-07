from odoo import models, fields


class NotationWizard(models.TransientModel):
    """Read colour codes and look up dictionary entries interactively.

    Bridge modules extend it with company-data modes (e.g. verifying a
    PDP product's colour code).
    """
    _name = 'rubicon.notation.wizard'
    _description = 'Notation Transcribe & Verify'

    mode = fields.Selection([
        ('parse', 'Read a colour code'),
        ('lookup', 'Look up a name or code'),
    ], default='parse', required=True)
    code = fields.Char(string='Colour Code / Text')
    result = fields.Text(readonly=True)

    def action_run(self):
        self.ensure_one()
        self.result = '\n'.join(self._run_lines()) or 'Nothing to do.'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _run_lines(self):
        service = self.env['rubicon.notation']
        lines = []
        if self.mode == 'parse':
            for token in (self.code or '').strip().upper().split('+'):
                if not token:
                    continue
                parsed = service.parse_token(token)
                if parsed['problems']:
                    lines.append(f"{token}: " + '; '.join(parsed['problems']))
                    continue
                article = parsed['article']
                parts = [article.name]
                if parsed['grade']:
                    parts.append(f"grade {parsed['grade'].name}")
                if parsed['hue']:
                    parts.append(f"hue {parsed['hue'].name}")
                if article.implied_hue_id:
                    parts.append(f"implied hue {article.implied_hue_id.name}")
                shape = parsed['shape'] or article.default_shape_id
                if shape:
                    parts.append(f"shape {shape.name}")
                lines.append(f"{token}: " + ', '.join(parts))
        elif self.mode == 'lookup':
            found = service.lookup(self.code)
            for label, rows in (found or {}).items():
                if rows:
                    lines.append(label + ':')
                    lines.extend(f"  {code} = {name}" for code, name in rows)
            if not lines:
                lines.append('No match.')
        return lines
