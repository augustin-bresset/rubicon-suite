from odoo import api, fields, models


class EmasurConvertWizard(models.TransientModel):
    _name = 'emasur.convert.wizard'
    _description = 'Convert a code between the Rubicon and Emasur notations'

    direction = fields.Selection([
        ('to_emasur', 'Rubicon → Emasur'),
        ('from_emasur', 'Emasur → Rubicon'),
    ], required=True, default='to_emasur')
    kind = fields.Selection([
        ('design', 'Design / product code'),
        ('stone', 'Stone code'),
    ], required=True, default='design')
    input_code = fields.Char(string='Code', required=True)
    result = fields.Char(readonly=True)
    details = fields.Text(readonly=True)

    def action_convert(self):
        self.ensure_one()
        converter = self.env['emasur.converter']
        code = (self.input_code or '').strip()
        if self.kind == 'design':
            method = (converter.design_to_emasur if self.direction == 'to_emasur'
                      else converter.design_from_emasur)
            outcome = method(code)
            self.result = outcome.get('code') or outcome.get('error')
            unknown = outcome.get('unknown')
            self.details = ('Unmapped tokens: %s — complete the Emasur stone list.'
                            % ', '.join(unknown)) if unknown else False
        elif self.direction == 'to_emasur':
            outcome = converter.stone_to_emasur(code)
            if outcome.get('error'):
                self.result, self.details = outcome['error'], False
            else:
                parts = [outcome.get('stone_code') or '?',
                         outcome.get('shape_code') or '?',
                         outcome.get('cut_code') or '?',
                         outcome.get('size') or '?']
                self.result = ' / '.join(parts)
                self.details = False if outcome.get('exact') else \
                    'Shade approximated by the generic species entry.'
        else:
            outcome = converter.stone_from_emasur(code)
            if outcome.get('error'):
                self.result, self.details = outcome['error'], False
            else:
                self.result = '%s (shade: %s)' % (
                    outcome['type_code'], outcome.get('shade_code') or 'any')
                candidates = outcome.get('candidate_stones')
                self.details = ('Matching Rubicon stones: %s' % ', '.join(candidates)
                                ) if candidates else 'No pdp.stone matches yet.'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
