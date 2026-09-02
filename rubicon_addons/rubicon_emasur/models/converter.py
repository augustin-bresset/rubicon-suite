from odoo import api, models


class EmasurConverter(models.AbstractModel):
    """Conversion between the Rubicon and Emasur notations.

    Works at three levels: the colour token of a design (a stone type code
    since the colour-code enforcement, a TYPE+SHADE compound in legacy
    codes), a full stone, and a whole design string MODEL-C1+C2+.../METAL.
    Unknown pieces are never guessed: they come back marked so the mapping
    tables can be completed instead.
    """
    _name = 'emasur.converter'
    _description = 'Rubicon/Emasur notation converter'

    # ── Stone level ────────────────────────────────────────────────────────
    @api.model
    def _emasur_entry(self, type_id, shade_id):
        Stone = self.env['emasur.stone']
        if shade_id:
            entry = Stone.search([('type_id', '=', type_id.id),
                                  ('shade_id', '=', shade_id.id)],
                                 order='code', limit=1)
            if entry:
                return entry, True
        entries = Stone.search([('type_id', '=', type_id.id),
                                ('shade_id', '=', False)])
        if not entries:
            # No generic species entry: fall back to any entry of the type.
            entries = Stone.search([('type_id', '=', type_id.id)])
        entry = min(entries, key=lambda e: (len(e.code), e.code)) if entries else entries
        return entry, False

    @api.model
    def stone_to_emasur(self, stone):
        """`stone`: a pdp.stone record or its code. Returns a dict with the
        Emasur components (or None where unmapped) and `exact` telling
        whether the shade matched or the generic species entry was used."""
        if isinstance(stone, str):
            record = self.env['pdp.stone'].search([('code', '=', stone)], limit=1)
            if not record:
                return {'error': 'unknown rubicon stone code: %s' % stone}
            stone = record
        entry, exact = self._emasur_entry(stone.type_id, stone.shade_id)
        shape_map = self.env['emasur.shape.map'].search(
            [('rubicon_shape_id', '=', stone.shape_id.id)], limit=1) if stone.shape_id else None
        return {
            'stone_code': entry.code if entry else None,
            'shape_code': shape_map.shape_id.code if shape_map and shape_map.shape_id else None,
            'cut_code': shape_map.cut_id.code if shape_map and shape_map.cut_id else None,
            'size': stone.size_id.name or None,
            'exact': bool(entry) and (exact or not stone.shade_id),
        }

    @api.model
    def stone_from_emasur(self, stone_code, shape_code=None, cut_code=None, size=None):
        """Returns the Rubicon reading of Emasur components: type/shade codes,
        the candidate Rubicon shapes and the matching pdp.stone codes."""
        entry = self.env['emasur.stone'].search([('code', '=', stone_code)], limit=1)
        if not entry:
            return {'error': 'unknown emasur stone code: %s' % stone_code}
        if not entry.type_id:
            return {'error': 'emasur stone %s is not mapped to a Rubicon type yet' % stone_code}
        map_domain = []
        if shape_code:
            map_domain.append(('shape_id.code', '=', shape_code))
        if cut_code:
            map_domain.append(('cut_id.code', '=', cut_code))
        shapes = self.env['emasur.shape.map'].search(map_domain).mapped(
            'rubicon_shape_id') if map_domain else self.env['pdp.stone.shape']
        domain = [('type_id', '=', entry.type_id.id)]
        if entry.shade_id:
            domain.append(('shade_id', '=', entry.shade_id.id))
        if shapes:
            domain.append(('shape_id', 'in', shapes.ids))
        if size:
            domain.append(('size_id.name', '=', size))
        candidates = self.env['pdp.stone'].search(domain, limit=20)
        return {
            'type_code': entry.type_id.code,
            'shade_code': entry.shade_id.code or None,
            'shape_codes': shapes.mapped('code'),
            'candidate_stones': candidates.mapped('code'),
        }

    # ── Colour-token level ─────────────────────────────────────────────────
    @api.model
    def _split_compound(self, token):
        """Legacy tokens glue TYPE and SHADE together (CITAAA, AGAWH).
        Longest type-code prefix wins; the remainder must be a shade code."""
        Type = self.env['pdp.stone.type']
        Shade = self.env['pdp.stone.shade']
        alias = self.env['emasur.token.alias'].search([('token', '=', token)], limit=1)
        if alias:
            return alias.type_id, alias.shade_id
        for length in range(len(token), 0, -1):
            stone_type = Type.search([('code', '=', token[:length])], limit=1)
            if not stone_type:
                continue
            rest = token[length:]
            if not rest:
                return stone_type, Shade
            shade = Shade.search([('code', '=', rest)], limit=1)
            if shade:
                return stone_type, shade
        return None, None

    @api.model
    def token_to_emasur(self, token):
        stone_type, shade = self._split_compound(token)
        if not stone_type:
            return None
        entry, _exact = self._emasur_entry(stone_type, shade or False)
        return entry.code if entry else None

    @api.model
    def token_from_emasur(self, code):
        """An Emasur code becomes the canonical Rubicon colour token: the
        bare stone type code (shades left the colour code with Lot 1)."""
        entry = self.env['emasur.stone'].search([('code', '=', code)], limit=1)
        return entry.type_id.code if entry and entry.type_id else None

    # ── Design level ───────────────────────────────────────────────────────
    @api.model
    def _convert_design(self, design, token_func):
        design = (design or '').strip()
        if '-' not in design:
            return {'error': 'not a MODEL-COLORS[/METAL] design: %s' % design}
        model_code, rest = design.split('-', 1)
        colors, _slash, metal = rest.rpartition('/')
        if not colors:
            colors, metal = rest, ''
        converted, unknown = [], []
        for token in [t for t in colors.split('+') if t]:
            target = token_func(token)
            if target:
                converted.append(target)
            else:
                converted.append('?%s?' % token)
                unknown.append(token)
        out = '%s-%s' % (model_code, '+'.join(converted))
        if metal:
            out += '/%s' % metal
        return {'code': out, 'unknown': unknown}

    @api.model
    def design_to_emasur(self, design):
        """MODEL and METAL are shared between the two companies and pass
        through unchanged; each colour token is translated."""
        return self._convert_design(design, self.token_to_emasur)

    @api.model
    def design_from_emasur(self, design):
        return self._convert_design(design, self.token_from_emasur)
