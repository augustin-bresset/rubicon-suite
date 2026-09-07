from odoo import models, fields, api


class SisDocumentAnalysis(models.Model):
    _inherit = 'sis.document'

    # Char, not Integer: an integer year renders as "2,025" in list views.
    analysis_year = fields.Char(
        string='Year',
        compute='_compute_analysis_year',
        store=True,
    )
    analysis_region_id = fields.Many2one(
        'res.country.group',
        string='Region',
        compute='_compute_analysis_region',
        store=True,
    )
    analysis_country_id = fields.Many2one(
        'res.country',
        string='Country',
        related='party_id.country_id',
        store=True,
    )

    @api.depends('date_created')
    def _compute_analysis_year(self):
        for rec in self:
            rec.analysis_year = str(rec.date_created.year) if rec.date_created else False

    @api.depends('party_id.country_id.country_group_ids')
    def _compute_analysis_region(self):
        for rec in self:
            rec.analysis_region_id = rec.party_id.country_id.country_group_ids[:1]
