from odoo import models, api


class NotationServicePdp(models.AbstractModel):
    """PDP-side services: legacy records to notation components and back."""
    _inherit = 'rubicon.notation'

    # ----------------------------------------------- legacy -> components

    @api.model
    def components_for(self, type_id, shade_id=None, shape_id=None):
        """Notation components of one legacy (type, shade, shape).

        Returns ``{'article', 'grade', 'hue', 'shape', 'problems'}`` with
        notation records (empty recordsets when absent or unmapped).
        """
        problems = []
        article = self.env['rubicon.notation.stone'].search(
            [('type_id', '=', type_id)], limit=1)
        if not article:
            type_rec = self.env['pdp.stone.type'].browse(type_id)
            problems.append(
                f"no article for stone type '{type_rec.code or type_id}'")
        grade = self.env['rubicon.notation.grade']
        hue = self.env['rubicon.notation.hue']
        if shade_id:
            mapping = self.env['rubicon.notation.shade.map'].search(
                [('shade_id', '=', shade_id)], limit=1)
            if mapping:
                grade, hue = mapping.grade_id, mapping.hue_id
            else:
                shade = self.env['pdp.stone.shade'].browse(shade_id)
                problems.append(f"shade '{shade.code}' is not mapped")
        shape = self.env['rubicon.notation.shape']
        if shape_id:
            shape = self.env['rubicon.notation.shape'].search(
                [('shape_id', '=', shape_id)], limit=1)
            if not shape:
                shape_rec = self.env['pdp.stone.shape'].browse(shape_id)
                problems.append(
                    f"shape '{shape_rec.code}' has no notation code")
        return {'article': article, 'grade': grade, 'hue': hue,
                'shape': shape, 'problems': problems}

    @api.model
    def build_token_legacy(self, type_id, shade_id=None, shape_id=None):
        """Token for one legacy (type, shade, shape)."""
        components = self.components_for(type_id, shade_id, shape_id)
        if not components['article']:
            type_rec = self.env['pdp.stone.type'].browse(type_id)
            return {'token': f"?{type_rec.code or type_id}?",
                    'problems': components['problems']}
        built = self.build_token(components['article'], components['grade'],
                                 components['hue'], components['shape'])
        built['problems'] = components['problems'] + built['problems']
        return built

    # ------------------------------------------------- product level

    @api.model
    def transcribe_product(self, product_id):
        """Colour code of a product's real composition, ordered center
        first then heaviest single stone descending."""
        product = self.env['pdp.product'].browse(product_id)
        composition = product.stone_composition_id
        if not composition:
            return {'code': '',
                    'problems': ['product has no stone composition']}
        problems = []
        entries = []
        for line in composition.stone_line_ids:
            stone = line.stone_id
            if not stone.type_id:
                continue
            built = self.build_token_legacy(
                stone.type_id.id, stone.shade_id.id, stone.shape_id.id)
            problems.extend(built['problems'])
            entries.append((built['token'],
                            composition._line_weight(line),
                            line.is_center))
        return {'code': '+'.join(self.order_tokens(entries)),
                'problems': problems}

    @api.model
    def verify_product(self, product_id, colour_code):
        """Is ``colour_code`` coherent with the product's composition?"""
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

    # --------------------------------------- dev-side code proposal (bulk)

    @api.model
    def action_propose_codes(self):
        """Prefill empty dictionaries with frequency-based proposals.

        Dev-side tool (Makefile / shell), never exposed in the UI. Stones
        and shapes get 2-letter codes mnemonic where possible, most-used
        first so frequent entries grab the natural letters; grades map the
        known legacy grade shades to digits; each article's default shape
        follows its usage. Hues and fused-shade mappings are left to human
        curation. Idempotent: existing rows are kept.
        """
        counts = {'stones': 0, 'shapes': 0, 'grades': 0}
        Stone = self.env['rubicon.notation.stone']
        Shape = self.env['rubicon.notation.shape']
        Grade = self.env['rubicon.notation.grade']
        Map = self.env['rubicon.notation.shade.map']

        self.env.cr.execute("""
            SELECT s.type_id, count(*) AS n,
                   mode() WITHIN GROUP (ORDER BY s.shade_id) AS shade,
                   mode() WITHIN GROUP (ORDER BY s.shape_id) AS shape
            FROM pdp_product_stone ps JOIN pdp_stone s ON s.id = ps.stone_id
            GROUP BY s.type_id ORDER BY n DESC""")
        stats = {r[0]: (r[2], r[3]) for r in self.env.cr.fetchall()}

        # Shapes first, so article defaults can point at them.
        staken = set(Shape.with_context(active_test=False)
                     .search([]).mapped('code'))
        smapped = set(Shape.search([('shape_id', '!=', False)])
                      .mapped('shape_id').ids)
        for shape_rec in self.env['pdp.stone.shape'].search([]):
            if shape_rec.id in smapped:
                continue
            code = self._propose_two_letters(shape_rec.code, staken)
            if not code:
                continue
            staken.add(code)
            Shape.create({'code': code, 'name': shape_rec.shape or shape_rec.code,
                          'shape_id': shape_rec.id})
            counts['shapes'] += 1

        taken = set(Stone.with_context(active_test=False)
                    .search([]).mapped('code'))
        mapped_types = set(Stone.search([('type_id', '!=', False)])
                           .mapped('type_id').ids)
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
            _shade, shape_id = stats.get(type_rec.id, (None, None))
            default_shape = Shape.search(
                [('shape_id', '=', shape_id)], limit=1) if shape_id else Shape
            Stone.create({'code': code, 'name': type_rec.name or type_rec.code,
                          'type_id': type_rec.id,
                          'default_shape_id': default_shape.id})
            counts['stones'] += 1

        # Grades: the known legacy quality shades, mapped as they come.
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
        import re
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
