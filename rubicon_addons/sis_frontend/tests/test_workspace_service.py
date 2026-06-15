from odoo.tests.common import TransactionCase


class TestSisWorkspaceService(TransactionCase):
    """Atomic-save service used by the SIS OWL workspace."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.svc = cls.env['sis.workspace.service']
        cls.Partner = cls.env['res.partner']
        cls.Document = cls.env['sis.document']
        cls.Item = cls.env['sis.document.item']

    # ---- party --------------------------------------------------------

    def test_save_party_creates_with_children(self):
        """A new party plus delivery/contact/bank are created and linked."""
        party_id = self.svc.save_party({
            'party_id': False,
            'party_vals': {'name': 'Acme Co', 'is_company': True},
            'delivery': {'id': False, 'vals': {'type': 'delivery', 'name': 'Acme Ship', 'city': 'Paris'}},
            'contact': {'id': False, 'vals': {'type': 'contact', 'name': 'Jane', 'is_company': False}},
            'bank': {'id': False, 'vals': {'acc_number': 'ACC-1', 'sis_bank_name': 'BNP'}},
        })
        party = self.Partner.browse(party_id)
        self.assertEqual(party.name, 'Acme Co')

        delivery = self.Partner.search([('parent_id', '=', party_id), ('type', '=', 'delivery')])
        self.assertEqual(delivery.city, 'Paris')
        contact = self.Partner.search([('parent_id', '=', party_id), ('type', '=', 'contact')])
        self.assertEqual(contact.name, 'Jane')
        bank = self.env['res.partner.bank'].search([('partner_id', '=', party_id)])
        self.assertEqual(bank.acc_number, 'ACC-1')

    def test_save_party_updates_existing(self):
        """An existing party id updates in place rather than duplicating."""
        party = self.Partner.create({'name': 'Before', 'is_company': True})
        before = self.Partner.search_count([])
        new_id = self.svc.save_party({
            'party_id': party.id,
            'party_vals': {'name': 'After', 'is_company': True},
        })
        self.assertEqual(new_id, party.id)
        self.assertEqual(party.name, 'After')
        self.assertEqual(self.Partner.search_count([]), before)

    def test_save_party_is_atomic_on_error(self):
        """A failing bank rolls back the party created earlier in the call."""
        before = self.Partner.search_count([])
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.svc.save_party({
                    'party_id': False,
                    'party_vals': {'name': 'Rollback Co', 'is_company': True},
                    'bank': {'id': False, 'vals': {'acc_number': 'X', 'no_such_field_zzz': 1}},
                })
        self.assertEqual(self.Partner.search_count([]), before,
                         "the party create must roll back with the failed bank")

    # ---- document -----------------------------------------------------

    def _customer(self):
        return self.Partner.create({'name': 'Doc Customer', 'is_company': True})

    def test_save_document_creates_with_items(self):
        """A new document and its items are created and linked."""
        customer = self._customer()
        res = self.svc.save_document({
            'id': False,
            'doc_vals': {'name': 'SQ-DOC-1', 'doc_type_code': 'SQ', 'party_id': customer.id},
            'deleted_items': [],
            'items': [
                {'id': False, 'vals': {'sequence': 10, 'design': 'A', 'qty': 1}},
                {'id': False, 'vals': {'sequence': 20, 'design': 'B', 'qty': 2}},
            ],
        })
        doc = self.Document.browse(res['id'])
        self.assertTrue(doc.exists())
        items = self.Item.search([('document_id', '=', doc.id)])
        self.assertEqual(len(items), 2)
        self.assertEqual(set(items.mapped('design')), {'A', 'B'})

    def test_save_document_deletes_and_updates_items(self):
        """Listed items are unlinked; an item carrying an id is updated."""
        customer = self._customer()
        doc = self.Document.create({'name': 'SQ-DOC-2', 'doc_type_code': 'SQ', 'party_id': customer.id})
        keep = self.Item.create({'document_id': doc.id, 'sequence': 10, 'design': 'keep', 'qty': 1})
        drop = self.Item.create({'document_id': doc.id, 'sequence': 20, 'design': 'drop', 'qty': 1})

        self.svc.save_document({
            'id': doc.id,
            'doc_vals': {'name': doc.name, 'party_id': customer.id},
            'deleted_items': [drop.id],
            'items': [{'id': keep.id, 'vals': {'sequence': 10, 'design': 'kept', 'qty': 5}}],
        })

        self.assertFalse(drop.exists())
        self.assertEqual(keep.design, 'kept')
        self.assertEqual(keep.qty, 5)

    def test_save_document_is_atomic_on_error(self):
        """A failing item rolls back the document created earlier in the call."""
        customer = self._customer()
        before = self.Document.search_count([])
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.svc.save_document({
                    'id': False,
                    'doc_vals': {'name': 'SQ-DOC-3', 'doc_type_code': 'SQ', 'party_id': customer.id},
                    'deleted_items': [],
                    'items': [{'id': False, 'vals': {'sequence': 10, 'no_such_field_zzz': 1}}],
                })
        self.assertEqual(self.Document.search_count([]), before,
                         "the document create must roll back with the failed item")
