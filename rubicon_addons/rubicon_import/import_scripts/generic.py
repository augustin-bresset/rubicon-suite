import csv
import os
import time
import re

from odoo import fields as odoo_fields

from ..tools.standard import create_stone_code

many2one_cache = {}

def is_empty(value):
    return value is None or str(value).strip() in ('', '\x00')

def resolve_many2one(env, field, raw_value):
    comodel = field.comodel_name
    rec_name = env[comodel]._rec_name
    raw_value = str(raw_value).strip()

    # Initialiser le cache pour ce comodel
    if comodel not in many2one_cache:
        print(f"[INFO] Loading {comodel} references via `{rec_name}`...")
        many2one_cache[comodel] = {
            str(r[rec_name]).strip(): r.id
            for r in env[comodel].search([])
        }

    # Résolution via cache
    result = many2one_cache[comodel].get(raw_value)
    if result is None:
        print(f"[WARN] Unresolved Many2one: {field.name} = '{raw_value}' in {comodel} using {rec_name}")
        return ''
    return result


def fields_type_to_func(env, field, value):
    if value in ('', None):
        return None
    if isinstance(field, odoo_fields.Float):
        return float(value)
    if isinstance(field, odoo_fields.Integer):
        return int(value)
    if field.type == 'many2one':
        return resolve_many2one(env, field, value)
    # if isinstance(field, odoo_fields.Char) and not field.name == "name":
    #     value = value.replace('  ', '')
    #     value = value.replace(' ', '_')
    #     return value
    return value


def import_csv(
    env, 
    model, 
    module='pdp_product',
    verbose=True, 
    batch_size=1000,
    register_xml_id=False, 
    fields_maj=None
    ):
    """
    Import CSV into a model with optional deferred write phase for specific fields.

    Args:
        env: Odoo environment
        model: env['my.model']
        module: name of the module (used for XML IDs)
        verbose: print import logs
        batch_size: number of records per create()
        rewrite: force updates if record already exists
        fields_maj: list of fields to skip during creation and patch afterward
    """
    import os
    import csv
    import time
    global many2one_cache
    many2one_cache = {}

    # Model = env[model._name]
    module_path = os.path.dirname(__file__)
    data_path = os.path.join(module_path, '../..', module, 'data', f'{model._name}.csv')

    start = time.time()
    logs = {"created": 0, "updated": 0, "skipped": 0, "total": 0}

    ref_cache = {}
    new_records = []
    new_xml_ids = []
    deferred_updates = []  # List of (xml_id, {field: value})

    with open(data_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

        if not rows:
            print("CSV file is empty.")
            return

        headers = rows[0][1:]  # skip XML ID
        
        for row in rows[1:]:
            logs['total'] += 1
            xml_id = row[0]
            field_values = row[1:]

            vals = {}
            deferred = {}
            skipped = False
            for field_name, raw_value in zip(headers, field_values):
 
                if not field_name:
                    continue
                field = model._fields.get(field_name)
                if not field:
                    continue
                if field.required and is_empty(raw_value):
                    print(f"[WARN] Row Skipped {row}")
                    skipped = True
                    break
                if fields_maj and field_name in fields_maj:
                    deferred[field_name] = raw_value
                else:
                    vals[field_name] = fields_type_to_func(env, field, raw_value)
                    if field.required and is_empty(vals[field_name]):
                        skipped = True
                        break
            if skipped:
                logs['skipped']+=1
                continue
            ref = ref_cache.get(xml_id)
            if ref is None:
                ref = env.ref(f"{module}.{xml_id}", raise_if_not_found=False)
                ref_cache[xml_id] = ref

            if ref: 
                ref.write(vals)
                if deferred:
                    for field_name in deferred.keys():
                        field = model._fields.get(field_name)
                        deferred[field_name] = fields_type_to_func(env, field, deferred[field_name])
                    ref.write(deferred)
                logs['updated'] += 1
            else:
                new_records.append(vals)
                new_xml_ids.append((xml_id, deferred))
                
                if len(new_records) >= batch_size:
                    created = model.create(new_records)
                    for rec, (xid, deferred) in zip(created, new_xml_ids):
                        if register_xml_id:
                            env['ir.model.data'].create({
                                'module': module,
                                'name': xid,
                                'model': model._name,
                                'res_id': rec.id,
                            })
                        if deferred:
                            deferred_updates.append((rec, deferred))
                    logs['created'] += len(created)
                    new_records = []
                    new_xml_ids = []

    # final flush
    if new_records:
        created = model.create(new_records)
        for rec, (xid, deferred) in zip(created, new_xml_ids):
            if register_xml_id:
                env['ir.model.data'].create({
                    'module': module,
                    'name': xid,
                    'model': model._name,
                    'res_id': rec.id,
                })
            if deferred:
                deferred_updates.append((rec, deferred))
        logs['created'] += len(created)

    # Phase 2: write deferred fields
    print(f"[INFO] Deferred size {len(deferred_updates)}")
    for rec, deferred in deferred_updates:
        # print(f"[INFO] {rec.id} updated with {deferred_vals}")
        for field_name in deferred.keys():
            field = model._fields.get(field_name)    
            deferred[field_name] = fields_type_to_func(env, field, deferred[field_name])
        rec.write(deferred)

    duration = time.time() - start

    if verbose:
        print(f"Import for {model._name}:")
        print(f"  => Total rows    : {logs['total']}")
        print(f"  => Created       : {logs['created']}")
        print(f"  => Updated       : {logs['updated']}")
        print(f"  => Skipped       : {logs['skipped']}")
        print(f"  => Time elapsed  : {duration:.2f} seconds")

    return logs

