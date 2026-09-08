from odoo import models, fields, api


class NotationWizard(models.TransientModel):
    """Both directions of the notation, interactively: pick a stone's
    components and get its code, or type a code and read it back.

    Bridge modules extend it with company-data modes (e.g. verifying a
    PDP product's colour code).
    """
    _name = 'rubicon.notation.wizard'
    _description = 'Notation Transcribe & Verify'

    mode = fields.Selection([
        ('compose', 'Compose a code from a stone'),
        ('parse', 'Read a colour code'),
        ('lookup', 'Look up a name or code'),
    ], default='compose', required=True)
    code = fields.Char(string='Colour Code / Text')
    article_id = fields.Many2one('rubicon.notation.stone', string='Stone')
    grade_id = fields.Many2one('rubicon.notation.grade', string='Grade')
    hue_id = fields.Many2one('rubicon.notation.hue', string='Hue')
    shape_id = fields.Many2one('rubicon.notation.shape', string='Shape')
    result = fields.Text(readonly=True)

    @api.onchange('mode', 'article_id', 'grade_id', 'hue_id', 'shape_id')
    def _onchange_components(self):
        # Compose mode answers live, without pressing Run.
        if self.mode == 'compose' and self.article_id:
            self.result = '\n'.join(self._compose_lines())

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

    def _compose_lines(self):
        service = self.env['rubicon.notation']
        built = service.build_token(self.article_id, self.grade_id,
                                    self.hue_id, self.shape_id)
        lines = [f"Code: {built['token']}"]
        omitted = []
        if self.grade_id and self.grade_id == self.article_id.default_grade_id:
            omitted.append(f"grade {self.grade_id.code} (default)")
        if self.hue_id and self.hue_id in (self.article_id.implied_hue_id,
                                           self.article_id.default_hue_id):
            omitted.append(f"hue {self.hue_id.code} (implied/default)")
        if self.shape_id and self.shape_id == self.article_id.default_shape_id:
            omitted.append(f"shape {self.shape_id.code} (default)")
        if omitted:
            lines.append('Omitted: ' + ', '.join(omitted))
        lines.extend(f"Problem: {p}" for p in built['problems'])
        return lines

    def _run_lines(self):
        service = self.env['rubicon.notation']
        lines = []
        if self.mode == 'compose':
            if not self.article_id:
                return ['Pick a stone first.']
            return self._compose_lines()
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
