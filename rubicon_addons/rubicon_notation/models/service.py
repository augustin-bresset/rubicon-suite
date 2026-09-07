import re

from odoo import models, api

TWO_LETTERS = re.compile(r'^[A-Z]{2}$')


class NotationService(models.AbstractModel):
    """Grammar engine of the notation: parse, build, order, look up.

    A token reads ``PP[G][BB][EE]`` — article (2 letters), grade (1 digit),
    hue (digit+letter), shape (2 letters) — blocks omitted when they match
    the article's defaults. The block widths and character classes make
    every token parse without separators: after the article, a candidate
    split is valid only if the widths sum to the remaining length and each
    block matches its class, and at most one split can (grade is a lone
    digit, a hue starts with a digit and ends with a letter, a shape is
    letters only).

    A colour code joins the distinct stone tokens with ``+``, ordered
    center stone first, then heaviest single stone descending (ties by
    token). This core works purely on notation records; translating a
    company's own product data into notation components is the job of a
    bridge module (rubicon_notation_pdp for the Rubicon PDP).
    """
    _name = 'rubicon.notation'
    _description = 'Notation Service'

    # ------------------------------------------------------------- parsing

    @api.model
    def _split_rest(self, rest):
        """All (grade, hue, shape) splits of the after-article part."""
        valid = []
        for g in (0, 1):
            for b in (0, 2):
                for e in (0, 2):
                    if g + b + e != len(rest):
                        continue
                    grade = rest[:g]
                    hue = rest[g:g + b]
                    shape = rest[g + b:]
                    if g and not grade.isdigit():
                        continue
                    if b and not (hue[0].isdigit() and hue[1].isalpha()):
                        continue
                    if e and not shape.isalpha():
                        continue
                    valid.append((grade, hue, shape))
        return valid

    @api.model
    def parse_token(self, token):
        """Parse one stone token against the dictionaries.

        Returns the matched records (empty recordsets for absent blocks)
        and ``problems`` — empty when everything resolved.
        """
        result = {
            'token': (token or '').strip().upper(),
            'article': self.env['rubicon.notation.stone'],
            'grade': self.env['rubicon.notation.grade'],
            'hue': self.env['rubicon.notation.hue'],
            'shape': self.env['rubicon.notation.shape'],
            'problems': [],
        }
        token = result['token']
        if len(token) < 2 or not TWO_LETTERS.match(token[:2]):
            result['problems'].append(
                f"'{token}': a token starts with a 2-letter article code")
            return result
        splits = self._split_rest(token[2:])
        if len(splits) != 1:
            result['problems'].append(
                f"'{token}': not a valid PP[G][BB][EE] token")
            return result
        grade_code, hue_code, shape_code = splits[0]

        article = self.env['rubicon.notation.stone'].search(
            [('code', '=', token[:2])], limit=1)
        if not article:
            result['problems'].append(f"unknown article '{token[:2]}'")
        result['article'] = article

        if grade_code:
            result['grade'] = self.env['rubicon.notation.grade'].search(
                [('code', '=', grade_code)], limit=1)
            if not result['grade']:
                result['problems'].append(f"unknown grade '{grade_code}'")
        if hue_code:
            result['hue'] = self.env['rubicon.notation.hue'].search(
                [('code', '=', hue_code)], limit=1)
            if not result['hue']:
                result['problems'].append(f"unknown hue '{hue_code}'")
            elif article and article.implied_hue_id:
                result['problems'].append(
                    f"'{token}': article {article.code} already implies hue "
                    f"{article.implied_hue_id.code} — double colour")
        if shape_code:
            result['shape'] = self.env['rubicon.notation.shape'].search(
                [('code', '=', shape_code)], limit=1)
            if not result['shape']:
                result['problems'].append(f"unknown shape '{shape_code}'")
        return result

    # ------------------------------------------------------------ building

    @api.model
    def build_token(self, article, grade=None, hue=None, shape=None):
        """Token from notation records (or ids); defaults omitted.

        Returns ``{'token', 'problems'}``. A hue equal to the article's
        implied or default hue is omitted; a different one is a double
        colour when the article implies a hue.
        """
        Stone = self.env['rubicon.notation.stone']
        article = article if isinstance(article, models.BaseModel) \
            else Stone.browse(article)
        grade = self._as_record('rubicon.notation.grade', grade)
        hue = self._as_record('rubicon.notation.hue', hue)
        shape = self._as_record('rubicon.notation.shape', shape)
        problems = []
        parts = [article.code]
        if grade and grade != article.default_grade_id:
            parts.append(grade.code)
        if hue and hue != article.implied_hue_id and hue != article.default_hue_id:
            if article.implied_hue_id:
                problems.append(
                    f"article {article.code} already implies hue "
                    f"{article.implied_hue_id.code} — double colour")
            parts.append(hue.code)
        if shape and shape != article.default_shape_id:
            parts.append(shape.code)
        return {'token': ''.join(parts), 'problems': problems}

    @api.model
    def _as_record(self, model, value):
        if isinstance(value, models.BaseModel):
            return value
        return self.env[model].browse(value) if value else self.env[model]

    # ------------------------------------------------------------ ordering

    @api.model
    def order_tokens(self, entries):
        """Distinct tokens ordered: center first, then heaviest single
        stone descending, ties by token. ``entries`` — (token, weight,
        is_center) triples."""
        max_by_token = {}
        center = None
        for token, weight, is_center in entries:
            if not token:
                continue
            if token not in max_by_token or weight > max_by_token[token]:
                max_by_token[token] = weight
            if is_center:
                center = token
        ordered = sorted(
            (token for token in max_by_token if token != center),
            key=lambda token: (-max_by_token[token], token),
        )
        return ([center] if center else []) + ordered

    @api.model
    def transcribe(self, components):
        """Colour code from notation components.

        ``components`` — dicts with ``article`` (record or id), optional
        ``grade``/``hue``/``shape``, ``weight``, ``is_center``. Returns
        ``{'code', 'problems'}``.
        """
        problems = []
        entries = []
        for component in components:
            built = self.build_token(component['article'],
                                     component.get('grade'),
                                     component.get('hue'),
                                     component.get('shape'))
            problems.extend(built['problems'])
            entries.append((built['token'],
                            component.get('weight') or 0.0,
                            bool(component.get('is_center'))))
        return {'code': '+'.join(self.order_tokens(entries)),
                'problems': problems}

    # ------------------------------------------------------ reverse lookup

    @api.model
    def lookup(self, text):
        """Name or code to dictionary entries, both directions, all axes."""
        text = (text or '').strip()
        if not text:
            return {}
        domain = ['|', ('code', 'ilike', text), ('name', 'ilike', text)]
        return {
            'stones': [(s.code, s.name)
                       for s in self.env['rubicon.notation.stone'].search(
                           domain, limit=10)],
            'grades': [(g.code, g.name)
                       for g in self.env['rubicon.notation.grade'].search(
                           domain, limit=10)],
            'hues': [(h.code, h.name)
                     for h in self.env['rubicon.notation.hue'].search(
                         domain, limit=10)],
            'shapes': [(s.code, s.name)
                       for s in self.env['rubicon.notation.shape'].search(
                           domain, limit=10)],
        }
