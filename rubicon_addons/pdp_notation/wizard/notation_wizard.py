from odoo import models, fields


class NotationWizard(models.TransientModel):
    """Transcribe, look up and verify notation codes interactively."""
    _name = 'pdp.notation.wizard'
    _description = 'Notation Transcribe & Verify'

    mode = fields.Selection([
        ('parse', 'Read a colour code'),
        ('lookup', 'Look up a name or code'),
        ('product', 'Verify a product'),
    ], default='parse', required=True)
    code = fields.Char(string='Colour Code / Text')
    product_id = fields.Many2one('pdp.product', string='Product')
    result = fields.Text(readonly=True)

    def action_run(self):
        self.ensure_one()
        service = self.env['pdp.notation']
        lines = []
        if self.mode == 'parse':
            for token in (self.code or '').strip().upper().split('+'):
                if not token:
                    continue
                parsed = service.parse_token(token)
                if parsed['problems']:
                    lines.append(f"{token}: " + '; '.join(parsed['problems']))
                else:
                    article = parsed['article']
                    parts = [f"{article.type_id.name or article.type_id.code}"]
                    if parsed['grade']:
                        parts.append(f"grade {parsed['grade'].name}")
                    if parsed['hue']:
                        parts.append(f"hue {parsed['hue'].name}")
                    if article.implied_hue_id:
                        parts.append(f"implied hue {article.implied_hue_id.name}")
                    shape = parsed['shape'].shape_id or article.default_shape_id
                    if shape:
                        parts.append(f"shape {shape.code}")
                    lines.append(f"{token}: " + ', '.join(parts))
        elif self.mode == 'lookup':
            found = service.lookup(self.code)
            for label, rows in (found or {}).items():
                if rows:
                    lines.append(label + ':')
                    lines.extend(f"  {row[0]} = {' / '.join(str(v) for v in row[1:])}"
                                 for row in rows)
            if not lines:
                lines.append('No match.')
        elif self.mode == 'product':
            if not self.product_id:
                lines.append('Pick a product first.')
            else:
                verdict = service.verify_product(self.product_id.id,
                                                 self.code or '')
                lines.append(f"Expected: {verdict['expected'] or '(none)'}")
                lines.append(f"Given:    {verdict['given'] or '(none)'}")
                lines.append('Coherent.' if verdict['ok'] else 'NOT coherent:')
                lines.extend(f"  - {p}" for p in verdict['problems'])
        self.result = '\n'.join(lines) or 'Nothing to do.'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
