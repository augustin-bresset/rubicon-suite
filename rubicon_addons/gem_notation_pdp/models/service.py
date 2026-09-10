from odoo import models, api


class NotationServicePdp(models.AbstractModel):
    """PDP-side services: legacy records to notation components and back."""
    _inherit = 'gem.notation'

    # ----------------------------------------------- legacy -> components

    @api.model
    def components_for(self, type_id, shade_id=None, shape_id=None):
        """Notation components of one legacy (type, shade, shape).

        Returns ``{'article', 'grade', 'hue', 'shape', 'problems'}`` with
        notation records (empty recordsets when absent or unmapped).
        """
        problems = []
        article = self.env['gem.notation.stone'].search(
            [('type_id', '=', type_id)], limit=1)
        if not article:
            type_rec = self.env['pdp.stone.type'].browse(type_id)
            problems.append(
                f"no article for stone type '{type_rec.code or type_id}'")
        grade = self.env['gem.notation.grade']
        hue = self.env['gem.notation.hue']
        if shade_id:
            mapping = self.env['gem.notation.shade.map'].search(
                [('shade_id', '=', shade_id)], limit=1)
            if mapping:
                grade, hue = mapping.grade_id, mapping.hue_id
            else:
                shade = self.env['pdp.stone.shade'].browse(shade_id)
                problems.append(f"shade '{shade.code}' is not mapped")
        shape = self.env['gem.notation.shape']
        if shape_id:
            shape = self.env['gem.notation.shape'].search(
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

    # ------------------------------------------- correspondence health

    @api.model
    def action_check_correspondence(self):
        """Gaps in the notation<->PDP correspondence; all zeros = every
        legacy record still resolves in the new notation."""
        queries = {
            'types_without_article': """
                SELECT count(*) FROM pdp_stone_type t
                WHERE NOT EXISTS (SELECT 1 FROM gem_notation_stone s
                                  WHERE s.type_id = t.id)""",
            'shades_unmapped': """
                SELECT count(*) FROM pdp_stone_shade sh
                WHERE NOT EXISTS (SELECT 1 FROM gem_notation_shade_map m
                                  WHERE m.shade_id = sh.id)""",
            'shapes_unlinked': """
                SELECT count(*) FROM pdp_stone_shape sp
                WHERE NOT EXISTS (SELECT 1 FROM gem_notation_shape s
                                  WHERE s.shape_id = sp.id)""",
        }
        result = {}
        for key, query in queries.items():
            self.env.cr.execute(query)
            result[key] = self.env.cr.fetchall()[0][0]
        return result

    # --------------------------------------- dev-side code proposal (bulk)

    TONE_WORDS = ('light', 'medium', 'dark', 'darker', 'good', 'bad')
    COLOUR_WORDS = ('blue', 'pink', 'green', 'black', 'brown', 'white',
                    'grey', 'gray', 'olive', 'lemon', 'smokey', 'smoky',
                    'champaign', 'champagne', 'yellow', 'red', 'orange',
                    'purple', 'violet')

    @api.model
    def action_propose_codes(self):
        """Prefill the dictionaries with frequency-based proposals so that
        EVERY legacy record has a correspondence.

        Dev-side tool (Makefile / shell), never exposed in the UI. Stones
        and shapes get 2-letter codes mnemonic where possible, most-used
        first so frequent entries grab the natural letters; grades map the
        known legacy grade shades to digits; every remaining legacy shade
        is decomposed into hue and/or grade (fused labels like 'Pink
        Light' split, the tone word matching a grade); hues get digit+
        initial codes (Pink -> 1P); colour-bearing type names propose the
        article's implied hue; and each article's defaults (shape, grade,
        hue) follow its actual usage. Proposals, not truth: review them in
        the dictionary screens. Idempotent: existing rows are kept.
        """
        counts = {'stones': 0, 'shapes': 0, 'grades': 0, 'hues': 0,
                  'shade_maps': 0, 'implied': 0, 'defaults': 0,
                  'relinked': 0}
        Stone = self.env['gem.notation.stone']
        Shape = self.env['gem.notation.shape']
        Grade = self.env['gem.notation.grade']
        Map = self.env['gem.notation.shade.map']

        # Phase 0 — relink: entries shipped as module data carry no PDP
        # link; match them by name before anything else, so they are
        # completed instead of duplicated.
        linked_types = set(Stone.search([('type_id', '!=', False)])
                           .mapped('type_id').ids)
        for stone in Stone.with_context(active_test=False).search(
                [('type_id', '=', False)]):
            type_rec = self.env['pdp.stone.type'].search(
                [('name', '=ilike', stone.name)], limit=1)
            if type_rec and type_rec.id not in linked_types:
                stone.type_id = type_rec
                linked_types.add(type_rec.id)
                if not stone.category_id and type_rec.category_id:
                    stone.category_id = self._category_for(type_rec)
                counts['relinked'] += 1
        linked_shapes = set(Shape.search([('shape_id', '!=', False)])
                            .mapped('shape_id').ids)
        for shape in Shape.search([('shape_id', '=', False)]):
            shape_rec = self.env['pdp.stone.shape'].search(
                ['|', ('shape', '=ilike', shape.name),
                 ('code', '=ilike', shape.name)], limit=1)
            if shape_rec and shape_rec.id not in linked_shapes:
                shape.shape_id = shape_rec
                linked_shapes.add(shape_rec.id)
                counts['relinked'] += 1

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
                          'category_id': self._category_for(type_rec).id,
                          'default_shape_id': default_shape.id})
            counts['stones'] += 1

        # Grades: fixed mapping - colour depth first (A->1 ... AAAA->4),
        # then the quality judgement scale used on precious stones
        # (2 Good->5, 3 Medium->6, C Bad->7).
        GRADE_MAP = [('A', '1'), ('AA', '2'), ('AAA', '3'), ('AAAA', '4'),
                     ('2', '5'), ('3', '6'), ('C', '7')]
        if not Grade.search_count([]):
            for legacy, digit in GRADE_MAP:
                shade = self.env['pdp.stone.shade'].search(
                    [('code', '=', legacy)], limit=1)
                if not shade:
                    continue
                words = (shade.shade or '').split()
                label = ' '.join(words[1:]) if words and words[0].upper() == legacy \
                    else (shade.shade or legacy)
                grade = Grade.create({'code': digit, 'name': label or legacy})
                if not Map.search([('shade_id', '=', shade.id)]):
                    Map.create({'shade_id': shade.id, 'grade_id': grade.id})
                counts['grades'] += 1

        # Every remaining shade decomposes into hue and/or grade. Grade
        # information may appear as an explicit code word (Grey AAA) or as
        # a tone word (Pink Light); species words never belong in a hue
        # name (White Sapphire -> White).
        GRADE_WORDS = {'a': 'A', 'aa': 'AA', 'aaa': 'AAA', 'aaaa': 'AAAA',
                       '2': '2', '3': '3', 'c': 'C'}
        TONE_TO_GRADE = {'light': 'A', 'medium': 'AA', 'dark': 'AAA',
                         'darker': 'AAAA', 'good': '2', 'bad': 'C'}
        grade_by_legacy = {
            legacy: Grade.search([('code', '=', digit)], limit=1)
            for legacy, digit in GRADE_MAP}
        species_words = set()
        for type_rec in self.env['pdp.stone.type'].search([]):
            for word in (type_rec.name or '').lower().split():
                if len(word) > 2 and word not in self.COLOUR_WORDS:
                    species_words.add(word)
        mapped_shades = set(Map.search([]).mapped('shade_id').ids)
        for shade in self.env['pdp.stone.shade'].search([]):
            if shade.id in mapped_shades:
                continue
            # A shade whose CODE is itself a grade code maps directly -
            # never through the tone words ('3 Medium' is the quality
            # scale, not the AA colour depth).
            direct = GRADE_WORDS.get((shade.code or '').lower())
            if direct and grade_by_legacy.get(direct):
                Map.create({'shade_id': shade.id,
                            'grade_id': grade_by_legacy[direct].id})
                counts['shade_maps'] += 1
                continue
            tokens = (shade.shade or shade.code or '').split()
            if tokens and tokens[0].upper() == (shade.code or '').upper():
                tokens = tokens[1:]     # drop the leading pseudo-code word
            grade_code = None
            hue_words = []
            for token in tokens:
                lowered = token.lower()
                if grade_code is None and lowered in GRADE_WORDS:
                    grade_code = GRADE_WORDS[lowered]
                elif grade_code is None and lowered in TONE_TO_GRADE:
                    grade_code = TONE_TO_GRADE[lowered]
                elif lowered in ('color', 'colour') or lowered in species_words:
                    continue
                else:
                    hue_words.append(token)
            grade = grade_by_legacy.get(grade_code) if grade_code else None
            hue_name = ' '.join(hue_words)
            if not hue_name and not grade:
                hue_name = shade.shade or shade.code
            hue = self._find_or_create_hue(hue_name, counts) if hue_name else None
            Map.create({'shade_id': shade.id,
                        'grade_id': grade.id if grade else False,
                        'hue_id': hue.id if hue else False})
            counts['shade_maps'] += 1

        # Colour-bearing type names propose the article's implied hue.
        for article in Stone.search([('implied_hue_id', '=', False),
                                     ('type_id', '!=', False)]):
            words = (article.name or '').split()
            if len(words) >= 2 and words[0].lower() in self.COLOUR_WORDS:
                article.implied_hue_id = self._find_or_create_hue(
                    words[0].title(), counts)
                counts['implied'] += 1

        # Article defaults follow the most-used shade of the type.
        for article in Stone.search([('type_id', '!=', False)]):
            shade_id = stats.get(article.type_id.id, (None, None))[0]
            if not shade_id:
                continue
            mapping = Map.search([('shade_id', '=', shade_id)], limit=1)
            updates = {}
            if mapping.grade_id and not article.default_grade_id:
                updates['default_grade_id'] = mapping.grade_id.id
            if (mapping.hue_id and not article.default_hue_id
                    and mapping.hue_id != article.implied_hue_id):
                updates['default_hue_id'] = mapping.hue_id.id
            if updates:
                article.write(updates)
                counts['defaults'] += 1
        return counts

    @api.model
    def _category_for(self, type_rec):
        Category = self.env['gem.notation.category']
        if not type_rec.category_id:
            return Category
        category = Category.search(
            [('name', '=ilike', type_rec.category_id.name)], limit=1)
        return category or Category.create(
            {'code': type_rec.category_id.code,
             'name': type_rec.category_id.name})

    @api.model
    def _find_or_create_hue(self, name, counts):
        """Existing hue by name (case-insensitive), else create one with a
        digit + initial code (Pink -> 1P, Purple -> 2P...)."""
        Hue = self.env['gem.notation.hue']
        hue = Hue.search([('name', '=ilike', name)], limit=1)
        if hue:
            return hue
        initial = next((c for c in name.upper() if c.isalpha()), 'X')
        taken = set(Hue.search([]).mapped('code'))
        code = next((f"{d}{initial}" for d in '123456789'
                     if f"{d}{initial}" not in taken), None)
        if not code:
            code = next(f"{d}{chr(letter)}" for d in '123456789'
                        for letter in range(65, 91)
                        if f"{d}{chr(letter)}" not in taken)
        counts['hues'] += 1
        return Hue.create({'code': code, 'name': name})

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
