import re

from odoo import models, api

TWO_LETTERS = re.compile(r'^[A-Z]{2}$')


class NotationService(models.AbstractModel):
    """Grammar engine of the notation: parse, build, transcribe, verify.

    A token reads ``PP[G][BB][EE]`` — article (2 letters), grade (1 digit),
    hue (digit+letter), shape (2 letters) — blocks omitted when they match
    the article's defaults. The block widths and character classes make
    every token parse without separators: after the article, a candidate
    split is valid only if the widths sum to the remaining length and each
    block matches its class, and at most one split can (grade is a lone
    digit, a hue starts with a digit and ends with a letter, a shape is
    letters only).

    A colour code joins the distinct stone tokens with ``+``, ordered like
    the legacy colour code: center stone first, then heaviest single stone
    descending (ties by token).
    """
    _name = 'pdp.notation'
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
        """Parse one stone token.

        Returns a dict with the matched dictionary records (empty recordsets
        when a block is absent), the resolved legacy fields, and
        ``problems`` — a list of strings, empty when everything resolved.
        """
        result = {
            'token': (token or '').strip().upper(),
            'article': self.env['pdp.notation.stone'],
            'grade': self.env['pdp.notation.grade'],
            'hue': self.env['pdp.notation.hue'],
            'shape': self.env['pdp.notation.shape'],
            'type_id': False, 'shade_id': False, 'shape_id': False,
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

        article = self.env['pdp.notation.stone'].search(
            [('code', '=', token[:2])], limit=1)
        if not article:
            result['problems'].append(f"unknown article '{token[:2]}'")
        result['article'] = article
        result['type_id'] = article.type_id.id

        if grade_code:
            result['grade'] = self.env['pdp.notation.grade'].search(
                [('code', '=', grade_code)], limit=1)
            if not result['grade']:
                result['problems'].append(f"unknown grade '{grade_code}'")
        if hue_code:
            result['hue'] = self.env['pdp.notation.hue'].search(
                [('code', '=', hue_code)], limit=1)
            if not result['hue']:
                result['problems'].append(f"unknown hue '{hue_code}'")
            elif article and article.implied_hue_id:
                result['problems'].append(
                    f"'{token}': article {article.code} already implies hue "
                    f"{article.implied_hue_id.code} — double colour")
        if shape_code:
            result['shape'] = self.env['pdp.notation.shape'].search(
                [('code', '=', shape_code)], limit=1)
            if not result['shape']:
                result['problems'].append(f"unknown shape '{shape_code}'")
            result['shape_id'] = result['shape'].shape_id.id

        # Legacy shade: explicit blocks win, else the article's default.
        if result['grade'] or result['hue']:
            mapping = self.env['pdp.notation.shade.map'].search([
                ('grade_id', '=', result['grade'].id or False),
                ('hue_id', '=', result['hue'].id or False),
            ], limit=1)
            if mapping:
                result['shade_id'] = mapping.shade_id.id
            else:
                result['problems'].append(
                    f"'{token}': no legacy shade maps to this grade/hue pair")
        elif article:
            result['shade_id'] = article.default_shade_id.id
            if not shape_code:
                result['shape_id'] = article.default_shape_id.id
        if article and not shape_code:
            result['shape_id'] = article.default_shape_id.id
        return result

    # ------------------------------------------------------------ building

    @api.model
    def build_token(self, type_id, shade_id=None, shape_id=None):
        """Token for one legacy (type, shade, shape). Returns
        ``{'token', 'problems'}`` — the token still renders with a
        placeholder block when a mapping is missing."""
        problems = []
        article = self.env['pdp.notation.stone'].search(
            [('type_id', '=', type_id)], limit=1)
        if not article:
            type_rec = self.env['pdp.stone.type'].browse(type_id)
            return {'token': f"?{type_rec.code or type_id}?",
                    'problems': [f"no article for stone type "
                                 f"'{type_rec.code or type_id}'"]}
        grade = hue = None
        if shade_id and shade_id != article.default_shade_id.id:
            mapping = self.env['pdp.notation.shade.map'].search(
                [('shade_id', '=', shade_id)], limit=1)
            if not mapping:
                shade = self.env['pdp.stone.shade'].browse(shade_id)
                problems.append(f"shade '{shade.code}' is not mapped")
            else:
                grade, hue = mapping.grade_id, mapping.hue_id
                if hue and article.implied_hue_id:
                    problems.append(
                        f"article {article.code} already implies hue "
                        f"{article.implied_hue_id.code} — double colour "
                        f"(shade '{mapping.shade_id.code}')")
        shape_part = ''
        if shape_id and shape_id != article.default_shape_id.id:
            shape = self.env['pdp.notation.shape'].search(
                [('shape_id', '=', shape_id)], limit=1)
            if not shape:
                shape_rec = self.env['pdp.stone.shape'].browse(shape_id)
                problems.append(f"shape '{shape_rec.code}' has no notation code")
            else:
                shape_part = shape.code
        token = (article.code + (grade.code if grade else '')
                 + (hue.code if hue else '') + shape_part)
        return {'token': token, 'problems': problems}

    # -------------------------------------------------- colour code (order)

    @api.model
    def transcribe_lines(self, entries):
        """Colour code from stone entries.

        ``entries`` — dicts with ``type_id``, ``shade_id``, ``shape_id``,
        ``weight``, ``is_center``. Returns ``{'code', 'problems'}``; the
        ordering is the legacy rule (center first, heaviest single stone
        descending) applied to the built tokens.
        """
        problems = []
        ordered_entries = []
        for entry in entries:
            if not entry.get('type_id'):
                continue
            built = self.build_token(entry['type_id'], entry.get('shade_id'),
                                     entry.get('shape_id'))
            problems.extend(built['problems'])
            ordered_entries.append((built['token'],
                                    entry.get('weight') or 0.0,
                                    bool(entry.get('is_center'))))
        Composition = self.env['pdp.product.stone.composition']
        code = '+'.join(Composition._order_color_codes(ordered_entries))
        return {'code': code, 'problems': problems}

    @api.model
    def transcribe_product(self, product_id):
        """Colour code of a product's real composition."""
        product = self.env['pdp.product'].browse(product_id)
        composition = product.stone_composition_id
        if not composition:
            return {'code': '', 'problems': ['product has no stone composition']}
        entries = [{
            'type_id': line.stone_id.type_id.id,
            'shade_id': line.stone_id.shade_id.id,
            'shape_id': line.stone_id.shape_id.id,
            'weight': composition._line_weight(line),
            'is_center': line.is_center,
        } for line in composition.stone_line_ids]
        return self.transcribe_lines(entries)

    # ----------------------------------------------------------- verifying

    @api.model
    def verify_product(self, product_id, colour_code):
        """Is ``colour_code`` coherent with the product's composition?

        Compares the given code with the transcription of the real stones,
        under the established ordering. Returns ``{'ok', 'expected',
        'given', 'problems'}``.
        """
        expected = self.transcribe_product(product_id)
        problems = list(expected['problems'])
        given_tokens = [t for t in
                        (colour_code or '').strip().upper().split('+') if t]
        for token in given_tokens:
            problems.extend(self.parse_token(token)['problems'])
        given = '+'.join(given_tokens)
        if not problems and given != expected['code']:
            if sorted(given_tokens) == sorted(expected['code'].split('+')):
                problems.append(
                    f"stones match but the order does not — expected "
                    f"'{expected['code']}' (center first, then heaviest)")
            else:
                problems.append(
                    f"stones do not match the composition — expected "
                    f"'{expected['code']}'")
        return {'ok': not problems, 'expected': expected['code'],
                'given': given, 'problems': problems}

    # ------------------------------------------------------ reverse lookup

    @api.model
    def lookup(self, text):
        """Name/code to dictionary entries, both directions, all axes."""
        text = (text or '').strip()
        if not text:
            return {}
        results = {}
        Stone = self.env['pdp.notation.stone']
        stones = Stone.search(['|', ('code', 'ilike', text),
                               ('type_id.code', 'ilike', text)], limit=10)
        if not stones:
            stones = Stone.search([('type_id.name', 'ilike', text)], limit=10)
        results['stones'] = [(s.code, s.type_id.code, s.type_id.name)
                             for s in stones]
        results['grades'] = [
            (g.code, g.name) for g in self.env['pdp.notation.grade'].search(
                ['|', ('code', 'ilike', text), ('name', 'ilike', text)], limit=10)]
        results['hues'] = [
            (h.code, h.name) for h in self.env['pdp.notation.hue'].search(
                ['|', ('code', 'ilike', text), ('name', 'ilike', text)], limit=10)]
        results['shapes'] = [
            (s.code, s.shape_id.code) for s in self.env['pdp.notation.shape'].search(
                ['|', ('code', 'ilike', text),
                 ('shape_id.code', 'ilike', text)], limit=10)]
        return results

    # --------------------------------------- dev-side code proposal (bulk)

    @api.model
    def action_propose_codes(self):
        """Prefill empty dictionaries with frequency-based proposals.

        Dev-side tool (Makefile / shell), never exposed in the UI. Stones
        and shapes get 2-letter codes mnemonic where possible, most-used
        first so frequent entries grab the natural letters; grades map the
        known legacy grade shades to digits. Hues and fused-shade mappings
        are left to human curation. Idempotent: existing rows are kept.
        """
        counts = {'stones': 0, 'shapes': 0, 'grades': 0}
        Stone = self.env['pdp.notation.stone']
        taken = set(Stone.with_context(active_test=False).search([]).mapped('code'))
        mapped_types = set(Stone.with_context(active_test=False)
                           .search([]).mapped('type_id').ids)
        self.env.cr.execute("""
            SELECT s.type_id, count(*) AS n,
                   mode() WITHIN GROUP (ORDER BY s.shade_id) AS shade,
                   mode() WITHIN GROUP (ORDER BY s.shape_id) AS shape
            FROM pdp_product_stone ps JOIN pdp_stone s ON s.id = ps.stone_id
            GROUP BY s.type_id ORDER BY n DESC""")
        stats = {r[0]: (r[2], r[3]) for r in self.env.cr.fetchall()}
        ordered = list(stats) + [
            t for t in self.env['pdp.stone.type'].search([]).ids
            if t not in stats]
        for type_rec in self.env['pdp.stone.type'].browse(ordered):
            if type_rec.id in mapped_types:
                continue
            code = self._propose_two_letters(
                type_rec.name or type_rec.code, taken)
            if not code:
                continue
            taken.add(code)
            shade_id, shape_id = stats.get(type_rec.id, (None, None))
            Stone.create({'code': code, 'type_id': type_rec.id,
                          'default_shade_id': shade_id or False,
                          'default_shape_id': shape_id or False})
            counts['stones'] += 1
        Shape = self.env['pdp.notation.shape']
        staken = set(Shape.search([]).mapped('code'))
        smapped = set(Shape.search([]).mapped('shape_id').ids)
        for shape_rec in self.env['pdp.stone.shape'].search([]):
            if shape_rec.id in smapped:
                continue
            code = self._propose_two_letters(shape_rec.code, staken)
            if not code:
                continue
            staken.add(code)
            Shape.create({'code': code, 'shape_id': shape_rec.id})
            counts['shapes'] += 1
        # Grades: the known legacy quality shades, most used first.
        Grade = self.env['pdp.notation.grade']
        Map = self.env['pdp.notation.shade.map']
        if not Grade.search_count([]):
            digit = 1
            for shade in self.env['pdp.stone.shade'].search(
                    [('code', 'in', ['A', 'AA', 'AAA', 'AAAA', '2', '3', 'C'])],
                    order='code'):
                grade = Grade.create({'code': str(digit), 'name': shade.shade})
                if not Map.search([('shade_id', '=', shade.id)]):
                    Map.create({'shade_id': shade.id, 'grade_id': grade.id})
                counts['grades'] += 1
                digit += 1
        return counts

    @api.model
    def _propose_two_letters(self, name, taken):
        letters = re.sub(r'[^A-Z]', '', (name or '').upper())
        if len(letters) < 2:
            letters += 'XX'
        candidates = [letters[0] + letters[i] for i in range(1, len(letters))]
        candidates += [letters[0] + chr(c) for c in range(65, 91)]
        candidates += [chr(a) + chr(b)
                       for a in range(65, 91) for b in range(65, 91)]
        for candidate in candidates:
            if candidate not in taken:
                return candidate
        return None
