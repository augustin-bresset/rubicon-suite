from odoo import models, fields, api


class SisDocumentAnalysis(models.Model):
    _inherit = 'sis.document'

    analysis_year = fields.Integer(
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
            rec.analysis_year = rec.date_created.year if rec.date_created else 0

    @api.depends('party_id.country_id.country_group_ids')
    def _compute_analysis_region(self):
        for rec in self:
            rec.analysis_region_id = rec.party_id.country_id.country_group_ids[:1]
