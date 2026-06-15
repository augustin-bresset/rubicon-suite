from odoo import models, api


class PdpWorkspaceService(models.AbstractModel):
    """Atomic persistence for the PDP OWL workspace.

    The whole save runs in a single RPC call, so it shares one transaction:
    if any operation raises, Odoo rolls back every change made here, instead
    of leaving the product in a half-saved state (the previous client-side
    save issued one RPC per row and committed each independently).

    Value coercion stays on the client; this service only persists the row
    dicts it is given, so it introduces no change in field semantics.
    """
    _name = 'pdp.workspace.service'
    _description = 'PDP Workspace Atomic Save Service'

    # Deletion key (from the client payload) -> model to unlink.
    _DELETE_MODELS = {
        'metal': 'pdp.product.model.metal',
        'labor_model': 'pdp.labor.cost.model',
        'labor_product': 'pdp.labor.cost.product',
        'addon': 'pdp.addon.cost',
        'part': 'pdp.product.part',
        'stone': 'pdp.product.stone',
    }

    def _persist(self, model_name, rows, parent_field=None, parent_id=None):
        """Write existing rows and create new ones.

        Each row is a flat dict of field values plus ``id`` (truthy = update)
        and ``key`` (the client's temporary _key, echoed back for new rows).
        Returns {str(key): new_id} for the rows that were created.
        """
        Model = self.env[model_name]
        new_ids = {}
        for row in rows:
            vals = dict(row)
            rec_id = vals.pop('id', None)
            key = vals.pop('key', None)
            if rec_id:
                Model.browse(rec_id).write(vals)
            else:
                if parent_field:
                    vals[parent_field] = parent_id
                rec = Model.create(vals)
                if key is not None:
                    new_ids[str(key)] = rec.id
        return new_ids

    @api.model
    def save_product_workspace(self, payload):
        """Persist every pending workspace change atomically.

        Returns ``{'composition_id': int|False, 'new_ids': {collection: {key: id}}}``
        so the client can adopt the database ids of the rows it created.
        """
        model_id = payload.get('model_id')
        product_id = payload.get('product_id')

        # 1. Deletions first, so re-created unique keys don't collide.
        deleted = payload.get('deleted') or {}
        for key, model_name in self._DELETE_MODELS.items():
            ids = [i for i in (deleted.get(key) or []) if i]
            if ids:
                self.env[model_name].browse(ids).unlink()

        new_ids = {}
        composition_id = payload.get('composition_id') or False

        # 2. Stones — need a composition; create one lazily and link the product.
        stones = payload.get('stones') or []
        if stones:
            if not composition_id and product_id:
                product = self.env['pdp.product'].browse(product_id)
                comp_code = product.code or ('COMP-%s' % product_id)
                composition = self.env['pdp.product.stone.composition'].create({'code': comp_code})
                composition_id = composition.id
                product.write({'stone_composition_id': composition_id})
            created = self._persist('pdp.product.stone', stones,
                                    parent_field='composition_id', parent_id=composition_id)
            if created:
                new_ids['stones'] = created

        # 3. Model-level collections.
        created = self._persist('pdp.product.model.metal', payload.get('metals') or [],
                                parent_field='model_id', parent_id=model_id)
        if created:
            new_ids['metals'] = created
        created = self._persist('pdp.labor.cost.model', payload.get('labor_model') or [],
                                parent_field='model_id', parent_id=model_id)
        if created:
            new_ids['labor_model'] = created

        # 4. Product-level collections.
        if product_id:
            created = self._persist('pdp.labor.cost.product', payload.get('labor_product') or [],
                                    parent_field='product_id', parent_id=product_id)
            if created:
                new_ids['labor_product'] = created
            created = self._persist('pdp.addon.cost', payload.get('addons') or [],
                                    parent_field='product_id', parent_id=product_id)
            if created:
                new_ids['addons'] = created
            created = self._persist('pdp.product.part', payload.get('parts') or [],
                                    parent_field='product_id', parent_id=product_id)
            if created:
                new_ids['parts'] = created

        return {'composition_id': composition_id, 'new_ids': new_ids}
