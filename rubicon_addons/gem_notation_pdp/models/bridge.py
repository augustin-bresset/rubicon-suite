from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NotationStone(models.Model):
    """Link an article to the legacy PDP stone type it represents."""
    _inherit = 'gem.notation.stone'

    type_id = fields.Many2one('pdp.stone.type', string='PDP Stone Type',
                              ondelete='restrict', index=True)

    _sql_constraints = [
        ('type_uniq', 'unique(type_id)',
         'This stone type already has an article code.'),
    ]


class NotationShape(models.Model):
    """Link a notation shape to the legacy PDP shape."""
    _inherit = 'gem.notation.shape'

    shape_id = fields.Many2one('pdp.stone.shape', string='PDP Shape',
                               ondelete='restrict', index=True)

    _sql_constraints = [
        ('shape_uniq', 'unique(shape_id)',
         'This shape already has a notation code.'),
    ]


class NotationShadeMap(models.Model):
    """How a legacy PDP shade reads in the new notation.

    A pure grade shade maps to a grade, a pure hue shade to a hue, and a
    fused legacy shade (PL = Pink Light) to both at once. Unmapped shades
    make the transcription report a problem instead of guessing.
    """
    _name = 'gem.notation.shade.map'
    _description = 'Notation Shade Mapping (PDP)'
    _rec_name = 'shade_id'
    _order = 'shade_id'

    _sql_constraints = [
        ('shade_uniq', 'unique(shade_id)', 'This shade is already mapped.'),
    ]

    shade_id = fields.Many2one('pdp.stone.shade', string='PDP Shade',
                               required=True, ondelete='cascade', index=True)
    grade_id = fields.Many2one('gem.notation.grade', string='Grade')
    hue_id = fields.Many2one('gem.notation.hue', string='Hue')

    @api.constrains('grade_id', 'hue_id')
    def _check_target(self):
        for rec in self:
            if not rec.grade_id and not rec.hue_id:
                raise ValidationError(
                    "A shade mapping must set a grade, a hue, or both.")
