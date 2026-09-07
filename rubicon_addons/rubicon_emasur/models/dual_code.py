from odoo import api, fields, models

SYSTEM_PARAM = 'rubicon_notation.system'


class EmasurCodeMixin(models.AbstractModel):
    """Dual notation: the record keeps its Rubicon code and carries the
    Emasur one next to it — nothing is ever renamed in place.

    - `alt_code` stays empty until the new system is delivered; it is
      loaded then (import or script), never invented by the converter.
    - Searching by name finds the record through either code
      (`_rec_names_search` on the concrete models).
    - The displayed code follows the `rubicon_notation.system` parameter
      ('rubicon' or 'emasur'); a record without an Emasur code falls back
      to its Rubicon code, so switching is safe while partially loaded.
    """
    _name = 'emasur.code.mixin'
    _description = 'Dual Rubicon/Emasur code'

    # Registry of the known notation systems: key -> (label, code field).
    # 'rubicon' is the native `code` field. Adding a system means adding a
    # Char field through this mixin's inheritors and one entry here — the
    # display, the search and the switch wizard follow from the registry.
    # One column per system on purpose: indexed, importable, no generic
    # code table to join through.
    NOTATION_SYSTEMS = {
        'rubicon': ('Rubicon (legacy codes)', 'code'),
        'alternative': ('Alternative (new system, fallback to legacy when empty)', 'alt_code'),
    }

    # One alternative code per record, with its provenance. Raw dictionary
    # elements (stones, metals) get codes ASSIGNED by the new system —
    # loading them marks the source official. Composed codes (products,
    # designs) are COMPUTED from those elements by the converter; a
    # recompute never overwrites an official value. Any manual write or
    # import of alt_code counts as official.
    alt_code = fields.Char(string='Alternative Code', index=True, copy=False)
    alt_code_source = fields.Selection(
        [('official', 'Official'), ('computed', 'Computed')],
        string='Alternative Code Source', copy=False)

    def _alt_code_suggestion(self):
        """The converter's complete reading of this record's code, or
        False. No rule by default; composed models override it."""
        self.ensure_one()
        return False

    def _refresh_alt_code(self):
        """Recompute the non-official alternative codes of `self`."""
        for record in self:
            if record.alt_code_source == 'official':
                continue
            suggestion = record._alt_code_suggestion() or False
            if suggestion == (record.alt_code or False):
                continue
            super(EmasurCodeMixin, record).write({
                'alt_code': suggestion,
                'alt_code_source': 'computed' if suggestion else False,
            })

    def write(self, vals):
        if 'alt_code' in vals and 'alt_code_source' not in vals:
            vals = dict(vals, alt_code_source='official' if vals['alt_code'] else False)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [
            dict(vals, alt_code_source='official')
            if vals.get('alt_code') and not vals.get('alt_code_source') else vals
            for vals in vals_list]
        return super().create(vals_list)

    @api.model
    def action_recompute_alt_codes(self):
        """Recompute every non-official alternative code of the model;
        rerunnable after each round of mapping curation."""
        records = self.search([])
        records._refresh_alt_code()
        return len(records.filtered('alt_code')), len(records)

    @api.model
    def emasur_active_system(self):
        """The user's own preference wins; the global parameter (set from
        the Notation System wizard) is the company default."""
        system = self.env.user.notation_system or \
            self.env['ir.config_parameter'].sudo().get_param(SYSTEM_PARAM, 'rubicon')
        return system if system in self.NOTATION_SYSTEMS else 'rubicon'

    @api.model
    def get_notation_ui(self):
        """What a workspace needs to render and switch codes."""
        return {
            'active': self.emasur_active_system(),
            'systems': [[key, label] for key, (label, _field)
                        in self.NOTATION_SYSTEMS.items()],
        }

    @api.model
    def set_user_notation(self, system):
        """Store the current user's own display preference; falsy means
        follow the company default again."""
        if system and system not in self.NOTATION_SYSTEMS:
            return self.emasur_active_system()
        self.env.user.write({'notation_system': system or False})
        return self.emasur_active_system()

    def _compute_display_name(self):
        super()._compute_display_name()
        system = self.emasur_active_system()
        field_name = self.NOTATION_SYSTEMS[system][1]
        if field_name != 'code':
            for record in self:
                if record[field_name]:
                    record.display_name = record[field_name]


class PdpProduct(models.Model):
    _name = 'pdp.product'
    _inherit = ['pdp.product', 'emasur.code.mixin']
    _rec_names_search = ['code', 'alt_code', 'legacy_code']

    def _alt_code_suggestion(self):
        self.ensure_one()
        if not self.code:
            return False
        outcome = self.env['emasur.converter'].design_to_emasur(self.code)
        code = outcome.get('code')
        return code if code and not outcome.get('unknown') else False

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        products._refresh_alt_code()
        return products

    def write(self, vals):
        result = super().write(vals)
        if 'code' in vals:
            self._refresh_alt_code()
        return result

    @api.model
    def action_recompute_alt_codes(self):
        """Set-based recompute over the whole catalog: the token map is
        built once, the composed codes are rebuilt in Python and written
        back by SQL join, official codes untouched. Seconds on 48k rows."""
        convert = self.env['emasur.converter']
        self.env.cr.execute("SELECT id, code FROM pdp_product WHERE code IS NOT NULL")
        rows = self.env.cr.fetchall()
        token_map, mapping = {}, []
        for record_id, code in rows:
            outcome, ok = [], True
            model_code, _sep, rest = code.partition('-')
            colors, _slash, metal = rest.rpartition('/')
            if not colors:
                colors, metal = rest, ''
            for token in [t for t in colors.split('+') if t]:
                if token not in token_map:
                    token_map[token] = convert.token_to_emasur(token)
                target = token_map[token]
                if not target:
                    ok = False
                    break
                outcome.append(target)
            if ok and outcome:
                alt = '%s-%s' % (model_code, '+'.join(outcome))
                if metal:
                    alt += '/%s' % metal
                mapping.append((record_id, alt))
        self.env.flush_all()
        self.env.cr.execute(
            """UPDATE pdp_product SET alt_code = NULL, alt_code_source = NULL
               WHERE alt_code_source = 'computed'""")
        for start in range(0, len(mapping), 5000):
            chunk = mapping[start:start + 5000]
            args = ','.join(
                self.env.cr.mogrify('(%s, %s)', pair).decode() for pair in chunk)
            self.env.cr.execute(
                """UPDATE pdp_product p SET alt_code = m.alt, alt_code_source = 'computed'
                   FROM (VALUES %s) AS m(id, alt)
                   WHERE p.id = m.id AND p.alt_code_source IS DISTINCT FROM 'official'""" % args)
        self.env.invalidate_all()
        return len(mapping), len(rows)


class PdpProductModel(models.Model):
    _name = 'pdp.product.model'
    _inherit = ['pdp.product.model', 'emasur.code.mixin']
    _rec_names_search = ['code', 'alt_code']


class PdpStone(models.Model):
    _name = 'pdp.stone'
    _inherit = ['pdp.stone', 'emasur.code.mixin']
    _rec_names_search = ['code', 'alt_code']


class PdpMetal(models.Model):
    _name = 'pdp.metal'
    _inherit = ['pdp.metal', 'emasur.code.mixin']
    _rec_names_search = ['code', 'alt_code']


class SisDocumentItem(models.Model):
    """Historical order lines stay written in the old notation; the
    converter's reading of each design is stored next to it, so the
    history answers searches in both systems. Only complete conversions
    are stored — a design with an unmapped token keeps an empty
    `alt_design` rather than a half-translated string."""
    _name = 'sis.document.item'
    _inherit = 'sis.document.item'
    _rec_names_search = ['design', 'alt_design']

    alt_design = fields.Char(string='Design (alternative notation)', index=True, copy=False)

    def _refresh_alt_design(self):
        convert = self.env['emasur.converter']
        for item in self:
            outcome = convert.design_to_emasur(item.design) if item.design else {}
            code = outcome.get('code')
            item.alt_design = code if code and not outcome.get('unknown') else False

    def report_design_lines(self):
        """Print the design in the notation asked by ``print_notation``.

        'legacy' (default) keeps the historical snapshot, 'alternative'
        prints the alternative code (falling back to the legacy one on a
        line that has none yet), and 'both' prints the legacy code with
        the alternative one under it.
        """
        self.ensure_one()
        lines = super().report_design_lines()
        notation = self.env.context.get('print_notation') or 'legacy'
        alt = self.alt_design or ''
        if not alt and notation in ('alternative', 'both') and self.design:
            # A line written before the latest mapping curation may not have
            # its conversion stored yet: try again at print time (still only
            # complete conversions — never half-translated codes).
            outcome = self.env['emasur.converter'].design_to_emasur(self.design)
            if outcome.get('code') and not outcome.get('unknown'):
                alt = outcome['code']
        if notation == 'alternative':
            return [alt] if alt else lines
        if notation == 'both' and alt and alt not in lines:
            return lines + [alt]
        return lines

    @api.model_create_multi
    def create(self, vals_list):
        items = super().create(vals_list)
        items.filtered('design')._refresh_alt_design()
        return items

    def write(self, vals):
        result = super().write(vals)
        if 'design' in vals:
            self._refresh_alt_design()
        return result

    @api.model
    def action_backfill_alt_design(self, batch_size=5000):
        """Fill alt_design over the whole history, set-based.

        Distinct designs are converted once each (the token map is warmed by
        the converter's own caches through repetition), then written back by
        SQL join — 200k+ lines take seconds, and rerunning after mapping
        curation only improves coverage. Returns (filled, distinct, total).
        """
        self.env.cr.execute("""
            SELECT design, count(*) FROM sis_document_item
            WHERE design IS NOT NULL AND design <> '' GROUP BY design
        """)
        rows = self.env.cr.fetchall()
        convert = self.env['emasur.converter']
        mapping, filled = [], 0
        for design, freq in rows:
            outcome = convert.design_to_emasur(design)
            code = outcome.get('code')
            if code and not outcome.get('unknown'):
                mapping.append((design, code))
                filled += freq
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE sis_document_item SET alt_design = NULL WHERE alt_design IS NOT NULL")
        for start in range(0, len(mapping), batch_size):
            chunk = mapping[start:start + batch_size]
            args = ','.join(
                self.env.cr.mogrify('(%s, %s)', pair).decode() for pair in chunk)
            self.env.cr.execute(
                "UPDATE sis_document_item i SET alt_design = m.emasur "
                "FROM (VALUES %s) AS m(design, emasur) WHERE i.design = m.design" % args)
        self.env.invalidate_all()
        total = sum(freq for _design, freq in rows)
        return filled, len(mapping), total


class EmasurSystemWizard(models.TransientModel):
    """One place to switch which notation the suite displays."""
    _name = 'emasur.system.wizard'
    _description = 'Active notation system'

    def _system_selection(self):
        return [(key, label) for key, (label, _field)
                in self.env['emasur.code.mixin'].NOTATION_SYSTEMS.items()]

    system = fields.Selection(
        selection=_system_selection, required=True,
        default=lambda self: self.env['emasur.code.mixin'].emasur_active_system())

    def action_apply(self):
        self.ensure_one()
        self.env['ir.config_parameter'].sudo().set_param(SYSTEM_PARAM, self.system)
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class ResUsers(models.Model):
    _inherit = 'res.users'

    notation_system = fields.Selection(
        selection=lambda self: [
            (key, label) for key, (label, _field)
            in self.env['emasur.code.mixin'].NOTATION_SYSTEMS.items()],
        string='Displayed Code System',
        help='Personal display preference; empty follows the company default '
             'set in the Emasur > Notation System wizard.')

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['notation_system']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['notation_system']
