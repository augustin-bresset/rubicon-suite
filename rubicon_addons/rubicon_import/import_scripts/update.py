import csv
import os
import time
# useful 
import re
from odoo import fields as odoo_fields

many2one_cache = {}

def is_empty(field):
    return field in {'', None, '\x00'}

def resolve_many2one(env, field, raw_value):
    comodel = field.comodel_name
    rec_name = env[comodel]._rec_name
    raw_value = str(raw_value).strip()

    if comodel not in many2one_cache:
        print(f"[INFO] Loading {comodel} references via `{rec_name}`...")
        many2one_cache[comodel] = {
            str(r[rec_name]).strip(): r.id
            for r in env[comodel].search([])
        }

    result = many2one_cache[comodel].get(raw_value)
    if result is None:
        print(f"[WARN] Unresolved Many2one: {field.name} = '{raw_value}' in {comodel} using {rec_name}")
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
    return value

def update_from_csv(env, model, datafile_path, mapping=None, match_field=None, verbose=True, batch_size=1000, filter=None):
    """
    Import or update model from CSV using a match_field (no XML ID, no deferred).

    Args:
        env: Odoo environment
        model: env['model.name']
        datafile_path: relative path to CSV file from rubicon_addons/
        mapping: dict from CSV header to model field
        match_field: model field to match for updates
        verbose: print results
        batch_size: bulk create size
    """
    global many2one_cache
    many2one_cache = {}

    Model = env[model._name]
    module_path = os.path.dirname(__file__)
    data_path = os.path.join(module_path, '../..', datafile_path)

    start = time.time()
    logs = {"created": 0, "updated": 0, "skipped": 0, "total": 0}
    create_batch = []

    with open(data_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        if not rows:
            print("CSV file is empty.")
            return

        headers = rows[0]

        for row in rows[1:]:
            logs['total'] += 1
            raw_dict = dict(zip(headers, row))
            vals = {}

            for csv_field, raw_value in raw_dict.items():
                if not csv_field or is_empty(raw_value):
                    continue

                model_field = mapping.get(csv_field)
                if model_field is None:
                    continue
                field = Model._fields.get(model_field)
                if not field:
                    continue
                if model_field in filter:
                    val = filter[model_field](raw_value)
                else:
                    val = raw_value
                if is_empty(val): continue
                vals[model_field] = fields_type_to_func(env, field, raw_value)
            if vals == {}:
                continue
            ref = None
            if match_field and match_field in vals:
                ref = Model.search([(match_field, '=', vals[match_field])], limit=1)

            if not ref:
                create_batch.append(vals)
                if len(create_batch) >= batch_size:                    
                    Model.create(create_batch)
                    logs['created'] += len(create_batch)
                    create_batch = []
    if len(create_batch) > 0:
        Model.create(create_batch)
        logs['created'] += len(create_batch)

    duration = time.time() - start
    if verbose:
        print(f"Import for {model._name}:")
        print(f"  => Total rows    : {logs['total']}")
        print(f"  => Created       : {logs['created']}")
        print(f"  => Updated       : {logs['updated']}")
        print(f"  => Time elapsed  : {duration:.2f} seconds")

    return logs
