from odoo import api, fields, models

SYSTEM_PARAM = 'rubicon_notation.system'


class EmasurCodeMixin(models.AbstractModel):
    """Dual notation: the record keeps its Rubicon code and carries the
    Emasur one next to it — nothing is ever renamed in place.

    - `emasur_code` stays empty until the new system is delivered; it is
      loaded then (import or script), never invented by the converter.
    - Searching by name finds the record through either code
      (`_rec_names_search` on the concrete models).
    - The displayed code follows the `rubicon_notation.system` parameter
      ('rubicon' or 'emasur'); a record without an Emasur code falls back
      to its Rubicon code, so switching is safe while partially loaded.
    """
    _name = 'emasur.code.mixin'
    _description = 'Dual Rubicon/Emasur code'

    emasur_code = fields.Char(string='Emasur Code', index=True, copy=False)

    @api.model
    def emasur_active_system(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            SYSTEM_PARAM, 'rubicon')

    def _compute_display_name(self):
        super()._compute_display_name()
        if self.emasur_active_system() == 'emasur':
            for record in self:
                if record.emasur_code:
                    record.display_name = record.emasur_code


class PdpProduct(models.Model):
    _name = 'pdp.product'
    _inherit = ['pdp.product', 'emasur.code.mixin']
    _rec_names_search = ['code', 'emasur_code']


class PdpProductModel(models.Model):
    _name = 'pdp.product.model'
    _inherit = ['pdp.product.model', 'emasur.code.mixin']
    _rec_names_search = ['code', 'emasur_code']


class PdpStone(models.Model):
    _name = 'pdp.stone'
    _inherit = ['pdp.stone', 'emasur.code.mixin']
    _rec_names_search = ['code', 'emasur_code']


class PdpMetal(models.Model):
    _name = 'pdp.metal'
    _inherit = ['pdp.metal', 'emasur.code.mixin']
    _rec_names_search = ['code', 'emasur_code']


class SisDocumentItem(models.Model):
    """Historical order lines stay written in the old notation; the
    converter's reading of each design is stored next to it, so the
    history answers searches in both systems. Only complete conversions
    are stored — a design with an unmapped token keeps an empty
    `design_emasur` rather than a half-translated string."""
    _name = 'sis.document.item'
    _inherit = 'sis.document.item'
    _rec_names_search = ['design', 'design_emasur']

    design_emasur = fields.Char(string='Design (Emasur)', index=True, copy=False)

    def _refresh_design_emasur(self):
        convert = self.env['emasur.converter']
        for item in self:
            outcome = convert.design_to_emasur(item.design) if item.design else {}
            code = outcome.get('code')
            item.design_emasur = code if code and not outcome.get('unknown') else False

    @api.model_create_multi
    def create(self, vals_list):
        items = super().create(vals_list)
        items.filtered('design')._refresh_design_emasur()
        return items

    def write(self, vals):
        result = super().write(vals)
        if 'design' in vals:
            self._refresh_design_emasur()
        return result

    @api.model
    def action_backfill_design_emasur(self, batch_size=5000):
        """Fill design_emasur over the whole history, set-based.

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
            "UPDATE sis_document_item SET design_emasur = NULL WHERE design_emasur IS NOT NULL")
        for start in range(0, len(mapping), batch_size):
            chunk = mapping[start:start + batch_size]
            args = ','.join(
                self.env.cr.mogrify('(%s, %s)', pair).decode() for pair in chunk)
            self.env.cr.execute(
                "UPDATE sis_document_item i SET design_emasur = m.emasur "
                "FROM (VALUES %s) AS m(design, emasur) WHERE i.design = m.design" % args)
        self.env.invalidate_all()
        total = sum(freq for _design, freq in rows)
        return filled, len(mapping), total


class EmasurSystemWizard(models.TransientModel):
    """One place to switch which notation the suite displays."""
    _name = 'emasur.system.wizard'
    _description = 'Active notation system'

    system = fields.Selection([
        ('rubicon', 'Rubicon (legacy codes)'),
        ('emasur', 'Emasur (new codes, fallback to legacy when empty)'),
    ], required=True, default=lambda self: self.env['emasur.code.mixin'].emasur_active_system())

    def action_apply(self):
        self.ensure_one()
        self.env['ir.config_parameter'].sudo().set_param(SYSTEM_PARAM, self.system)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
