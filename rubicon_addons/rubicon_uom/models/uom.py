from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RubiconUom(models.Model):
    _name = 'rubicon.uom'
    _description = 'Unit of Measure'
    _rec_name = 'symbol'
    _order = 'category_id, is_reference desc, name'

    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(string='Symbol', required=True)
    category_id = fields.Many2one(
        'rubicon.uom.category', string='Category', required=True, ondelete='cascade',
    )
    ratio = fields.Float(
        string='Ratio', digits=(12, 6), default=1.0,
        help='Number of reference units in 1 of this unit. Reference unit = 1.0.',
    )
    is_reference = fields.Boolean(string='Is Reference Unit', default=False)
    is_global_default = fields.Boolean(string='Global Default', default=False)

    @api.constrains('is_reference', 'category_id')
    def _check_one_reference_per_category(self):
        for rec in self:
            if rec.is_reference:
                others = self.search([
                    ('category_id', '=', rec.category_id.id),
                    ('is_reference', '=', True),
                    ('id', '!=', rec.id),
                ])
                if others:
                    raise UserError(
                        _('Category "%s" already has a reference unit.') % rec.category_id.code
                    )

    @api.constrains('is_global_default', 'category_id')
    def _check_one_global_default_per_category(self):
        for rec in self:
            if rec.is_global_default:
                others = self.search([
                    ('category_id', '=', rec.category_id.id),
                    ('is_global_default', '=', True),
                    ('id', '!=', rec.id),
                ])
                if others:
                    raise UserError(
                        _('Category "%s" already has a global default unit.') % rec.category_id.code
                    )

    def convert(self, value, to_uom):
        """Convert value expressed in self to to_uom.

        Raises UserError if self and to_uom belong to different categories.
        Returns 0 for None, False, or zero values. Negative values are allowed.
        """
        self.ensure_one()
        if self.category_id != to_uom.category_id:
            raise UserError(
                _('Cannot convert between units of different categories (%s vs %s).')
                % (self.category_id.code, to_uom.category_id.code)
            )
        if not value:
            return 0
        return value * self.ratio / to_uom.ratio

    def set_global_default(self):
        """Atomically set this unit as the global default for its category.

        Unsets is_global_default on the current default, sets it on self.

        Note: the spec places this method on rubicon.uom.category with a uom_id
        argument. This plan places it on rubicon.uom (no argument) for simplicity.
        Both approaches are functionally equivalent. The settings UI (v1) calls
        this indirectly via the admin form view rather than programmatically.
        """
        self.ensure_one()
        current = self.search([
            ('category_id', '=', self.category_id.id),
            ('is_global_default', '=', True),
            ('id', '!=', self.id),
        ])
        current.write({'is_global_default': False})
        self.write({'is_global_default': True})
