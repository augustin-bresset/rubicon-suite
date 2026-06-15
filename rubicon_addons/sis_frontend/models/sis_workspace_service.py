from odoo import models, api


class SisWorkspaceService(models.AbstractModel):
    """Atomic persistence for the SIS OWL workspace.

    Each save runs in a single RPC call, so it shares one transaction: if
    any operation raises, Odoo rolls back every change instead of leaving a
    half-written party (party saved, delivery/bank lost) or document
    (document saved, some items lost).

    Value coercion stays on the client; this service only persists the
    payload it is given, so it introduces no change in field semantics.
    """
    _name = 'sis.workspace.service'
    _description = 'SIS Workspace Atomic Save Service'

    @api.model
    def save_party(self, payload):
        """Persist a party and its delivery/contact/bank children atomically.

        The children carry their own ``vals`` and ``id`` (truthy = update);
        the parent link is set here so a freshly created party id propagates.
        Returns the party id.
        """
        Partner = self.env['res.partner']

        party_id = payload.get('party_id')
        party_vals = payload.get('party_vals') or {}
        if party_id:
            Partner.browse(party_id).write(party_vals)
        else:
            party_id = Partner.create(party_vals).id

        for key in ('delivery', 'contact'):
            child = payload.get(key)
            if not child:
                continue
            vals = dict(child.get('vals') or {})
            vals['parent_id'] = party_id
            if child.get('id'):
                Partner.browse(child['id']).write(vals)
            else:
                Partner.create(vals)

        bank = payload.get('bank')
        if bank:
            vals = dict(bank.get('vals') or {})
            vals['partner_id'] = party_id
            if bank.get('id'):
                self.env['res.partner.bank'].browse(bank['id']).write(vals)
            else:
                self.env['res.partner.bank'].create(vals)

        return party_id

    @api.model
    def save_document(self, payload):
        """Persist a document, its deleted items and its dirty items atomically.

        Returns ``{'id': doc_id, 'name': name}`` (name reflects backend
        auto-numbering applied on create).
        """
        Document = self.env['sis.document']
        Item = self.env['sis.document.item']

        doc_id = payload.get('id')
        doc_vals = payload.get('doc_vals') or {}
        if doc_id:
            doc = Document.browse(doc_id)
            doc.write(doc_vals)
        else:
            doc = Document.create(doc_vals)
            doc_id = doc.id

        deleted = [i for i in (payload.get('deleted_items') or []) if i]
        if deleted:
            Item.browse(deleted).unlink()

        for item in payload.get('items') or []:
            vals = dict(item.get('vals') or {})
            vals.pop('document_id', None)  # parent set here, never from the client
            if item.get('id'):
                Item.browse(item['id']).write(vals)
            else:
                vals['document_id'] = doc_id
                Item.create(vals)

        return {'id': doc_id, 'name': doc.name}
