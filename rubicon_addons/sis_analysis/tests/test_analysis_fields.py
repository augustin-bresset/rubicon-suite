from odoo.tests import common, tagged
from datetime import date


@tagged('post_install', '-at_install')
class TestSisDocumentAnalysisFields(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.region = self.env['res.country.group'].create({'name': '_Test Region'})
        self.country = self.env['res.country'].search([('code', '=', 'FR')], limit=1)
        self.country.country_group_ids = [(4, self.region.id)]
        self.partner = self.env['res.partner'].create({
            'name': '_Test Partner',
            'country_id': self.country.id,
        })

    def _make_doc(self, date_created=None, party_id=None):
        vals = {'name': '_TEST-'}
        if date_created:
            vals['date_created'] = date_created
        if party_id:
            vals['party_id'] = party_id
        return self.env['sis.document'].create(vals)

    def test_analysis_year_extracted_from_date(self):
        doc = self._make_doc(date_created=date(2023, 6, 15))
        self.assertEqual(doc.analysis_year, 2023)

    def test_analysis_year_is_zero_when_no_date(self):
        doc = self._make_doc()
        self.assertEqual(doc.analysis_year, 0)

    def test_analysis_region_id_from_first_country_group(self):
        doc = self._make_doc(date_created=date(2024, 1, 1), party_id=self.partner.id)
        self.assertEqual(doc.analysis_region_id, self.region)

    def test_analysis_region_id_false_when_partner_has_no_country(self):
        partner_no_country = self.env['res.partner'].create({'name': '_No Country'})
        doc = self._make_doc(date_created=date(2024, 1, 1), party_id=partner_no_country.id)
        self.assertFalse(doc.analysis_region_id)

    def test_analysis_region_id_false_when_no_party(self):
        doc = self._make_doc(date_created=date(2024, 1, 1))
        self.assertFalse(doc.analysis_region_id)

    def test_analysis_country_id_related_to_partner_country(self):
        doc = self._make_doc(date_created=date(2024, 1, 1), party_id=self.partner.id)
        self.assertEqual(doc.analysis_country_id, self.country)

    def test_analysis_country_id_false_when_no_party(self):
        doc = self._make_doc(date_created=date(2024, 1, 1))
        self.assertFalse(doc.analysis_country_id)
