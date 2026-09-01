from odoo import models, fields, api


class PcsDepartment(models.Model):
    """Production-flow helpers on top of the ps_utilities master data.

    A department belongs to one of two parallel tracks: the metal production
    chain ('prod') or the stone preparation chain ('stone'). A piece can be
    in one department of each track at the same time (its gold is cast while
    its stones are assorted), so scanning and dashboards are track-scoped.
    """
    _inherit = 'pcs.department'

    track = fields.Selection(
        [('prod', 'Production'), ('stone', 'Stone')],
        compute='_compute_track',
        help="Derived from the department group type: 'Stone' groups form the "
             "stone chain, everything else (Production, Prod + Stone) is the "
             "production chain.",
    )
    division_id = fields.Many2one(
        'pcs.division', string='Division', ondelete='set null',
        help="The workshop division this section belongs to: Stone, Metal, "
             "Assembly, or Quality Controller. Flow-less states (Cancel, "
             "Melting, Office...) belong to none.")
    is_qc = fields.Boolean(
        string='QC', compute='_compute_is_qc',
        help="Quality Controller checkpoint (division QC): performs the "
             "quality checks between production steps and hosts the two "
             "weighing scales (grams for metal, carats for stones).",
    )

    @api.depends('division_id.code')
    def _compute_is_qc(self):
        for dept in self:
            dept.is_qc = dept.division_id.code == 'QC'

    @api.depends('group_id.type')
    def _compute_track(self):
        for dept in self:
            dept.track = 'stone' if (dept.group_id.type or '') == 'Stone' else 'prod'

    def pbarcode_prefix(self):
        """Legacy PBarcode prefix, e.g. 'P01' for Wax or 'S01' for Assorting:
        track letter + zero-padded department sequence."""
        self.ensure_one()
        letter = 'S' if self.track == 'stone' else 'P'
        return '%s%02d' % (letter, self.sequence or 0)
