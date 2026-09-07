import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError

STONE_RE = re.compile(r'^[A-Z]{2}$')
GRADE_RE = re.compile(r'^[0-9]$')
HUE_RE = re.compile(r'^[0-9][A-Z]$')
SHAPE_RE = re.compile(r'^[A-Z]{2}$')


class NotationStone(models.Model):
    """Article of the new notation: the identity block PP (2 letters).

    One row per legacy stone type. A colour-bearing legacy type (Blue
    Topaz...) is folded through ``implied_hue_id``: its article is the base
    species and the hue is implied, so the new dictionary carries no
    colour+species compounds.
    """
    _name = 'pdp.notation.stone'
    _description = 'Notation Article (stone)'
    _rec_name = 'code'
    _order = 'code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The article code must be unique.'),
        ('type_uniq', 'unique(type_id)', 'This stone type already has an article code.'),
    ]

    code = fields.Char(required=True, index=True)
    type_id = fields.Many2one('pdp.stone.type', string='Stone Type',
                              required=True, ondelete='restrict', index=True)
    implied_hue_id = fields.Many2one(
        'pdp.notation.hue', string='Implied Hue',
        help="Set on colour-bearing legacy types (e.g. Blue Topaz): the "
             "article is the base species and this hue is implied by the "
             "type itself. A hue-mapped shade on such a stone is refused "
             "as a double colour.")
    default_shade_id = fields.Many2one(
        'pdp.stone.shade', string='Default Shade',
        help="Shade omitted from the token when the stone carries it.")
    default_shape_id = fields.Many2one(
        'pdp.stone.shape', string='Default Shape',
        help="Shape omitted from the token when the stone carries it.")
    active = fields.Boolean(default=True)

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if not STONE_RE.match(rec.code or ''):
                raise ValidationError(
                    "Article code must be exactly 2 uppercase letters (got %r)."
                    % rec.code)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} — {rec.type_id.name or rec.type_id.code}"


class NotationGrade(models.Model):
    """Quality grade: the G block (1 digit)."""
    _name = 'pdp.notation.grade'
    _description = 'Notation Grade'
    _rec_name = 'code'
    _order = 'code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The grade code must be unique.'),
    ]

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if not GRADE_RE.match(rec.code or ''):
                raise ValidationError(
                    "Grade code must be exactly 1 digit (got %r)." % rec.code)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} — {rec.name}"


class NotationHue(models.Model):
    """Hue: the BB block (digit + letter), so it always starts with a digit
    and every token parses without separators."""
    _name = 'pdp.notation.hue'
    _description = 'Notation Hue'
    _rec_name = 'code'
    _order = 'code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The hue code must be unique.'),
    ]

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if not HUE_RE.match(rec.code or ''):
                raise ValidationError(
                    "Hue code must be a digit followed by an uppercase letter "
                    "(got %r)." % rec.code)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} — {rec.name}"


class NotationShapeMap(models.Model):
    """Shape: the EE block (2 letters), mapped to a legacy shape."""
    _name = 'pdp.notation.shape'
    _description = 'Notation Shape'
    _rec_name = 'code'
    _order = 'code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The shape code must be unique.'),
        ('shape_uniq', 'unique(shape_id)', 'This shape already has a notation code.'),
    ]

    code = fields.Char(required=True, index=True)
    shape_id = fields.Many2one('pdp.stone.shape', string='Legacy Shape',
                               required=True, ondelete='restrict', index=True)

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if not SHAPE_RE.match(rec.code or ''):
                raise ValidationError(
                    "Shape code must be exactly 2 uppercase letters (got %r)."
                    % rec.code)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} — {rec.shape_id.code}"


class NotationShadeMap(models.Model):
    """How a legacy shade reads in the new notation.

    A pure grade shade maps to a grade, a pure hue shade to a hue, and a
    fused legacy shade (PL = Pink Light) to both at once. Unmapped shades
    make the transcription report a problem instead of guessing.
    """
    _name = 'pdp.notation.shade.map'
    _description = 'Notation Shade Mapping'
    _rec_name = 'shade_id'
    _order = 'shade_id'

    _sql_constraints = [
        ('shade_uniq', 'unique(shade_id)', 'This shade is already mapped.'),
    ]

    shade_id = fields.Many2one('pdp.stone.shade', string='Legacy Shade',
                               required=True, ondelete='cascade', index=True)
    grade_id = fields.Many2one('pdp.notation.grade', string='Grade')
    hue_id = fields.Many2one('pdp.notation.hue', string='Hue')

    @api.constrains('grade_id', 'hue_id')
    def _check_target(self):
        for rec in self:
            if not rec.grade_id and not rec.hue_id:
                raise ValidationError(
                    "A shade mapping must set a grade, a hue, or both.")
