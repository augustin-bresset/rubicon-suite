from psycopg2 import IntegrityError

from odoo.tests import common, tagged
from odoo import fields as odoo_fields
from odoo.tools import mute_logger


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
        doc = self._make_doc('SO-ZZQ-')
        self.assertEqual(doc.name, f'SO-ZZQ-{self.yy}001')

    def test_second_document_increments(self):
        self._make_doc('SO-ZZQ-')
        doc2 = self._make_doc('SO-ZZQ-')
        self.assertEqual(doc2.name, f'SO-ZZQ-{self.yy}002')

    def test_different_doc_type_independent_counter(self):
        self._make_doc('SO-ZZQ-')
        sq = self._make_doc('SQ-ZZQ-')
        self.assertEqual(sq.name, f'SQ-ZZQ-{self.yy}001')

    def test_different_client_independent_counter(self):
        self._make_doc('SO-ZZQ-')
        doc = self._make_doc('SO-ZZR-')
        self.assertEqual(doc.name, f'SO-ZZR-{self.yy}001')

    def test_complete_name_not_overwritten(self):
        doc = self.Doc.create({
            'name': 'SO-ZZQ-25099',
            'date_created': self.today,
        })
        self.assertEqual(doc.name, 'SO-ZZQ-25099')

    def test_doc_type_code_set_automatically(self):
        doc = self._make_doc('SO-ZZQ-')
        self.assertEqual(doc.doc_type_code, 'SO')

    def test_batch_create_gets_distinct_numbers(self):
        # Two partial names with the same prefix in ONE create() call must get
        # distinct running numbers (not both 001).
        docs = self.Doc.create([
            {'name': 'SO-ZZQ-', 'date_created': self.today},
            {'name': 'SO-ZZQ-', 'date_created': self.today},
        ])
        self.assertEqual(
            sorted(docs.mapped('name')),
            [f'SO-ZZQ-{self.yy}001', f'SO-ZZQ-{self.yy}002'])

    @mute_logger('odoo.sql_db')
    def test_duplicate_name_rejected(self):
        # A complete name colliding with an existing one is blocked by the
        # unique constraint rather than silently duplicated.
        self.Doc.create({'name': 'SO-ZZQ-99001', 'date_created': self.today})
        with self.assertRaises(IntegrityError):
            self.Doc.create({'name': 'SO-ZZQ-99001', 'date_created': self.today})
            self.env.flush_all()
