from odoo.tests import common, tagged
from odoo import fields as odoo_fields


@tagged('post_install', '-at_install')
class TestSisDocumentAutoNumber(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.Doc = self.env['sis.document']
        self.yy = str(odoo_fields.Date.today().year)[2:]
        self.today = odoo_fields.Date.today()


    def _make_doc(self, name_prefix):
        return self.Doc.create({
            'name': name_prefix,
            'date_created': self.today,
        })

    def test_first_document_gets_001(self):
        doc = self._make_doc('SO-EMA-')
        self.assertEqual(doc.name, f'SO-EMA-{self.yy}001')

    def test_second_document_increments(self):
        self._make_doc('SO-EMA-')
        doc2 = self._make_doc('SO-EMA-')
        self.assertEqual(doc2.name, f'SO-EMA-{self.yy}002')

    def test_different_doc_type_independent_counter(self):
        self._make_doc('SO-EMA-')
        sq = self._make_doc('SQ-EMA-')
        self.assertEqual(sq.name, f'SQ-EMA-{self.yy}001')

    def test_different_client_independent_counter(self):
        self._make_doc('SO-EMA-')
        doc = self._make_doc('SO-ABC-')
        self.assertEqual(doc.name, f'SO-ABC-{self.yy}001')

    def test_complete_name_not_overwritten(self):
        doc = self.Doc.create({
            'name': 'SO-EMA-25099',
            'date_created': self.today,
        })
        self.assertEqual(doc.name, 'SO-EMA-25099')

    def test_doc_type_code_set_automatically(self):
        doc = self._make_doc('SO-EMA-')
        self.assertEqual(doc.doc_type_code, 'SO')
