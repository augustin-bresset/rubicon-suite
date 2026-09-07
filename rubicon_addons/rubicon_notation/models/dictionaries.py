import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError

STONE_RE = re.compile(r'^[A-Z]{2}$')
GRADE_RE = re.compile(r'^[0-9]$')
HUE_RE = re.compile(r'^[0-9][A-Z]$')
SHAPE_RE = re.compile(r'^[A-Z]{2}$')


class NotationStone(models.Model):
    """Article: the identity block PP (2 letters).

    An article is a commercial stone identity (species or variety). A
    colour-bearing identity (Blue Topaz...) carries its hue through
    ``implied_hue_id``: the dictionary holds no colour+species compound
    and writing another hue on such an article is a double colour.
    Defaults are notation-level: a grade/hue/shape equal to the article's
    default is omitted from the token.
    """
    _name = 'rubicon.notation.stone'
    _description = 'Notation Article (stone)'
    _rec_name = 'code'
    _rec_names_search = ['code', 'name']
    _order = 'code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The article code must be unique.'),
    ]

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    implied_hue_id = fields.Many2one(
        'rubicon.notation.hue', string='Implied Hue',
        help="Hue carried by the identity itself (e.g. Blue Topaz). "
             "Writing another hue on this article is refused as a double "
             "colour.")
    default_grade_id = fields.Many2one('rubicon.notation.grade',
                                       string='Default Grade')
    default_hue_id = fields.Many2one('rubicon.notation.hue',
                                     string='Default Hue')
    default_shape_id = fields.Many2one('rubicon.notation.shape',
                                       string='Default Shape')
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
            rec.display_name = f"{rec.code} — {rec.name}"


class NotationGrade(models.Model):
    """Quality grade: the G block (1 digit)."""
    _name = 'rubicon.notation.grade'
    _description = 'Notation Grade'
    _rec_name = 'code'
    _rec_names_search = ['code', 'name']
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
    _name = 'rubicon.notation.hue'
    _description = 'Notation Hue'
    _rec_name = 'code'
    _rec_names_search = ['code', 'name']
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


class NotationShape(models.Model):
    """Shape: the EE block (2 letters)."""
    _name = 'rubicon.notation.shape'
    _description = 'Notation Shape'
    _rec_name = 'code'
    _rec_names_search = ['code', 'name']
    _order = 'code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The shape code must be unique.'),
    ]

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if not SHAPE_RE.match(rec.code or ''):
                raise ValidationError(
                    "Shape code must be exactly 2 uppercase letters (got %r)."
                    % rec.code)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} — {rec.name}"
