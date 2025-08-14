import csv
import os
import time
import re

from odoo import fields as odoo_fields

from ..tools.standard import create_stone_code

many2one_cache = {}

def is_empty(value):
    return value is None or str(value).strip() in ('', '\x00')

# def resolve_many2one(env, field, raw_value):
#     comodel = field.comodel_name
#     raw = str(raw_value).strip()
#     # cache initial
#     if comodel not in many2one_cache:
#         many2one_cache[comodel] = {}
#         for r in env[comodel].search([]):
#             # indexe par rec_name + code si dispo
#             many2one_cache[comodel][str(r.display_name).strip()] = r.id
#             if hasattr(r, 'name'):
#                 many2one_cache[comodel][str(r.name).strip()] = r.id
#             if hasattr(r, 'currency_unit_label'):
#                 many2one_cache[comodel][str(r.currency_unit_label).strip()] = r.id
#     result = many2one_cache[comodel].get(raw)
#     if result is None:
#         # fallback name_search
#         recs = env[comodel].name_search(raw, operator='=', limit=1)
#         if recs:
#             result = recs[0][0]
#             many2one_cache[comodel][raw] = result
#     if result is None:
#         print(f"[WARN] Unresolved Many2one: {field.name} = '{raw}' in {comodel}")
#         return ''
#     return result
    
    
def resolve_many2one(env, field, raw_value):
    """Resolve a M2O by rec_name, with robust fallbacks and inactive records."""
    comodel = field.comodel_name
    rec_name = env[comodel]._rec_name
    raw = '' if raw_value is None else str(raw_value).strip()

    if not raw:
        return ''

    # Normalise (évite les \ufeff, espaces, case)
    raw_norm = raw.replace('\ufeff', '').strip()
    raw_key = raw_norm.upper()

    # Init cache (inclut inactifs)
    if comodel not in many2one_cache:
        print(f"[INFO] Loading {comodel} references via `{rec_name}` (including inactive)...")
        m = env[comodel].with_context(active_test=False)
        cache = {}
        for r in m.search([]):
            # clé principale = rec_name
            key = str(r[rec_name]).strip().upper() if r[rec_name] else ''
            if key:
                cache[key] = r.id
            # cas res.currency : aussi indexer le symbole (฿, $, €)
            if comodel == 'res.currency':
                sym = getattr(r, 'symbol', None)
                if sym:
                    cache[str(sym).strip().upper()] = r.id
        many2one_cache[comodel] = cache

    # 1) Hit cache direct
    hit = many2one_cache[comodel].get(raw_key)
    if hit:
        return hit

    # 2) Accepter une valeur en XML-ID (ex: "base.THB")
    if '.' in raw_norm:
        try:
            rec = env.ref(raw_norm, raise_if_not_found=False)
            if rec and rec._name == comodel:
                many2one_cache[comodel][raw_key] = rec.id
                return rec.id
        except Exception:
            pass

    # 3) Fallback search strict (=) puis ilike
    m = env[comodel].with_context(active_test=False)
    domain_eq = [(rec_name, '=', raw_norm)]
    if comodel == 'res.currency':
        domain_eq = ['|', (rec_name, '=', raw_norm), ('symbol', '=', raw_norm)]

    rec = m.search(domain_eq, limit=1)
    if not rec:
        # dernier filet: ilike
        domain_ilike = [(rec_name, 'ilike', raw_norm)]
        if comodel == 'res.currency':
            domain_ilike = ['|', (rec_name, 'ilike', raw_norm), ('symbol', 'ilike', raw_norm)]
        rec = m.search(domain_ilike, limit=1)

    if rec:
        many2one_cache[comodel][raw_key] = rec.id
        return rec.id

    print(f"[WARN] Unresolved Many2one: {field.name} = '{raw_value}' in {comodel} using {rec_name}")
    return ''

    
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
    fields_maj=None,
    csv_path=None # Useful for testing
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
    if csv_path:
        data_path = csv_path
    else:
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

