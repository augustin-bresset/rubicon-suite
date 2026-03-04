"""
Convert raw SIS BCP CSV exports into Odoo-ready CSV format.

Source: data/backup_sis/*.csv (headerless BCP export)
Target: rubicon_addons/sis_party/data/*.csv and rubicon_addons/sis_document/data/*.csv

Usage: python3 -m rubicon_import.raw_to_data.raw_to_data_sis
"""

import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from rubicon_import.raw_to_data.raw_to_data import raw_to_data, backup_folder, root_folder

backup_sis = os.path.join(root_folder, 'data', 'backup_sis')
sis_party_data = os.path.join(root_folder, 'rubicon_addons', 'sis_party', 'data')
sis_doc_data = os.path.join(root_folder, 'rubicon_addons', 'sis_document', 'data')

os.makedirs(sis_party_data, exist_ok=True)
os.makedirs(sis_doc_data, exist_ok=True)


def s(val):
    """Strip whitespace and null bytes."""
    if val is None:
        return ''
    return str(val).strip().replace('\x00', '')


def safe_float(val, default=0.0):
    try:
        v = s(val)
        if not v:
            return default
        return float(v)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    try:
        v = s(val)
        if not v:
            return default
        return int(float(v))
    except (ValueError, TypeError):
        return default


def safe_date(val):
    """Parse MSSQL datetime string to YYYY-MM-DD."""
    v = s(val)
    if not v:
        return ''
    return v[:10]


def clean_phone(val):
    """Keep only digits and leading +, separated by space if multiple numbers."""
    v = s(val)
    if not v:
        return ''
    # Allowed chars: digits, +, space, comma (for split)
    # But user wants cleaning. Let's keep it simple:
    # 1. Split by comma or slash if present
    import re
    parts = re.split(r'[,/]', v)
    cleaned_parts = []
    for p in parts:
        # Keep digits and +
        clean = re.sub(r'[^0-9+]', '', p)
        if clean:
            cleaned_parts.append(clean)
    return ', '.join(cleaned_parts)

def clean_country(val):
    """Normalize country names."""
    v = s(val).strip()
    if not v:
        return ''
    # Map common variations/typos to standard names
    # This is a basic list, can be expanded
    mapping = {
        'Simba': 'Zimbabwe',
        'USA': 'United States',
        'UK': 'United Kingdom',
        # Add more as discovered
    }
    return mapping.get(v, v)

# ═══════════════════════════════════════════════════════
# Build lookup maps from raw CSVs (code/id → name)
# import_csv resolves Many2one via _rec_name, so we need
# the actual record names in the output CSV, not IDs.
# ═══════════════════════════════════════════════════════

def build_lookups():
    lookups = {}

    # Region: code → name
    lookups['region'] = {}
    with open(os.path.join(backup_sis, 'Regions.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                lookups['region'][s(row[0])] = s(row[1])

    # Country: code → name
    lookups['country'] = {}
    with open(os.path.join(backup_sis, 'Countries.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                lookups['country'][s(row[0])] = s(row[1])

    # PayTerm: id → name
    lookups['payterm'] = {}
    with open(os.path.join(backup_sis, 'PayTerms.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                lookups['payterm'][s(row[0])] = s(row[1])

    # Shipper: id → name
    lookups['shipper'] = {}
    with open(os.path.join(backup_sis, 'Shippers.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                lookups['shipper'][s(row[0])] = s(row[1])

    # Party: id → company name
    lookups['party'] = {}
    with open(os.path.join(backup_sis, 'Customers.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 3:
                pid = s(row[0])
                company = s(row[2])
                if pid and company:
                    lookups['party'][pid] = company

    print(f"[INFO] Lookups built: {', '.join(f'{k}={len(v)}' for k, v in lookups.items())}")
    return lookups


# ─── ROW CONVERTERS ───────────────────────────────────

def row_to_region(row):
    code = s(row[0])
    name = s(row[1])
    if not code:
        return None
    return {'id': f'sis_region_{code}', 'code': code, 'name': name}


def make_row_to_country(lookups):
    def row_to_country(row):
        code = s(row[0])
        name = s(row[1])
        region_code = s(row[2]) if len(row) > 2 else ''
        if not code:
            return None
        return {
            'id': f'sis_country_{code}',
            'code': code,
            'name': name,
            'region_id': lookups['region'].get(region_code, ''),
        }
    return row_to_country


def row_to_pay_term(row):
    pid = s(row[0])
    name = s(row[1])
    if not pid or not name:
        return None
    return {'id': f'sis_payterm_{pid}', 'name': name}


def row_to_shipper(row):
    sid = s(row[0])
    name = s(row[1])
    if not sid or not name:
        return None
    return {'id': f'sis_shipper_{sid}', 'name': name}


def make_row_to_trade_fair(lookups):
    def row_to_trade_fair(row):
        # Handle rows where name contains commas (BCP doesn't quote)
        # Normal: [id, name, country_code, city, date_start, date_end] => 6 cols
        # Shifted: extra comma in name => 7+ cols, detect by date pattern
        ncols = len(row)
        if ncols < 6:
            return None

        fid = s(row[0])
        if not fid:
            return None

        # Determine offset: find the first column that looks like a date (YYYY-)
        # starting from position 4 onwards
        offset = 0
        for i in range(4, min(ncols, 8)):
            val = s(row[i])
            if val and len(val) >= 10 and val[4] == '-':
                offset = i - 4  # position 4 should be date_start
                break

        name = s(','.join(row[1:2 + offset]))  # rejoin split name parts
        country_code = s(row[2 + offset]) if ncols > 2 + offset else ''
        city = s(row[3 + offset]) if ncols > 3 + offset else ''
        date_start = safe_date(row[4 + offset]) if ncols > 4 + offset else ''
        date_end = safe_date(row[5 + offset]) if ncols > 5 + offset else ''

        return {
            'id': f'sis_tradefair_{fid}',
            'name': name,
            'city': city,
            'country_id': lookups['country'].get(country_code, ''),
            'date_start': date_start,
            'date_end': date_end,
        }
    return row_to_trade_fair


def make_row_to_party(lookups):
    def row_to_party(row):
        if len(row) < 14:
            return None
        pid = s(row[0])
        code = s(row[1])
        company = s(row[2])
        if not pid or not company:
            return None

        country_code = s(row[13]) if len(row) > 13 else ''
        pay_term = s(row[21]) if len(row) > 21 else ''
        ship_method = s(row[22]) if len(row) > 22 else ''

        # Schema mappings:
        # row[24]: Inactive (bit) -> 1=Inactive, 0=Active
        # row[27]: Customer (bit) -> 1=Customer
        # row[28]: Vendor (bit) -> 1=Vendor

        inactive_bit = s(row[24]) == '1' if len(row) > 24 else False
        customer_bit = s(row[27]) == '1' if len(row) > 27 else False
        vendor_bit = s(row[28]) == '1' if len(row) > 28 else False
        
        is_active = not inactive_bit

        return {
            'id': f'sis_party_{pid}',
            'code': code,
            'company': company,
            'active': is_active,
            'customer_rank': 1 if customer_bit else 0,
            'supplier_rank': 1 if vendor_bit else 0,
            'contact_type': 'company' if code and code != '0' else 'individual',
            'is_company': True if code and code != '0' else False,
            'address': s(row[4]) if len(row) > 4 else '',
            'city': s(row[7]) if len(row) > 7 else '',
            'zip': s(row[8]) if len(row) > 8 else '',
            'country_id': lookups['country'].get(clean_country(s(row[13])), ''),
            'phone': clean_phone(row[14]) if len(row) > 14 else '',
            'homepage': s(row[15]) if len(row) > 15 else '',
            'fax': s(row[16]) if len(row) > 16 else '',
            'email': s(row[17]) if len(row) > 17 else '',
            'notes': s(row[18]) if len(row) > 18 else '',
            'group_code': s(row[20]) if len(row) > 20 else '',
            'pay_term_id': lookups['payterm'].get(pay_term, ''),
            'ship_method_id': lookups['shipper'].get(ship_method, ''),
            'ship_stamp': s(row[25]) if len(row) > 25 else '',
        }
    return row_to_party


def row_to_doc_type(row):
    code = s(row[0])
    name = s(row[1])
    category = s(row[2]) if len(row) > 2 else ''
    if not code:
        return None
    return {'id': f'sis_doctype_{code}', 'code': code, 'name': name, 'category': category}


def row_to_doc_in_mode(row):
    mid = s(row[0])
    name = s(row[1])
    if not mid:
        return None
    return {'id': f'sis_docinmode_{mid}', 'name': name}


def make_row_to_document(lookups):
    # DocType: code → name
    doc_type_lookup = {}
    with open(os.path.join(backup_sis, 'DocTypes.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                doc_type_lookup[s(row[0])] = s(row[1])

    def row_to_document(row):
        if len(row) < 30:
            return None
        doc_type = s(row[0])
        legacy_id = safe_int(row[1])
        doc_name = s(row[3])
        if not doc_type or not doc_name:
            return None
        # Validate doc_type - BCP multi-line text creates garbage rows
        if doc_type not in doc_type_lookup:
            return None

        xml_id = f'sis_doc_{doc_type}_{legacy_id}'
        party_raw = s(row[6])
        closed = s(row[9]) in ('1', 'True')
        canceled = s(row[10]) in ('1', 'True')

        return {
            'id': xml_id,
            'name': doc_name,
            'doc_type_code': doc_type,
            'doc_type_id': doc_type_lookup.get(doc_type, ''),
            'legacy_id': legacy_id,
            'date_created': safe_date(row[4]),
            'date_due': safe_date(row[5]),
            'party_id': lookups['party'].get(party_raw, ''),
            'party_code': party_raw,
            'margin_name': s(row[7]),
            'customer_po': s(row[8]),
            'closed': closed,
            'canceled': canceled,
            'employee': s(row[11]),
            'currency': s(row[19]),
            'total_qty': safe_int(safe_float(row[15])),
            'total_cost': safe_float(row[16]),
            'total_amount': safe_float(row[17]),
            'total_fob': safe_float(row[20]),
            'freight_insurance': safe_float(row[21]),
            'total_cif': safe_float(row[26]) if len(row) > 26 else 0.0,
            'notes': s(row[27]) if len(row) > 27 else '',
            'footnotes': s(row[28]) if len(row) > 28 else '',
        }
    return row_to_document


def make_row_to_doc_item():
    # Build (doc_type, legacy_id) → doc_name lookup from SalesDocs.csv
    doc_name_lookup = {}
    with open(os.path.join(backup_sis, 'SalesDocs.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 4:
                doc_type = s(row[0])
                legacy_id = safe_int(row[1])
                doc_name = s(row[3])
                if doc_type and legacy_id and doc_name:
                    doc_name_lookup[(doc_type, legacy_id)] = doc_name
    print(f"[INFO] Document name lookup built: {len(doc_name_lookup)} entries")

    counter = [0]

    def row_to_doc_item(row):
        if len(row) < 20:
            return None
        doc_type = s(row[0])
        doc_legacy_id = safe_int(row[1])
        design = s(row[4])
        if not doc_type or not doc_legacy_id:
            return None

        # Resolve document name for Many2one
        doc_name = doc_name_lookup.get((doc_type, doc_legacy_id), '')
        if not doc_name:
            return None  # Skip orphan items

        counter[0] += 1

        d = {
            'id': f'sis_item_{counter[0]}',
            'document_id': doc_name,
            'design': design,
            'ref_document': s(row[5]),
            'description': s(row[6]),
            'model_code': s(row[7]),
            'product_code': s(row[8]),
            'color_code': s(row[9]),
            'metal_code': s(row[10]),
            'purity': s(row[11]),
            'size_remarks': s(row[12]),
            'qty': safe_float(row[13]),
            'qty_shipped': safe_float(row[14]),
            'qty_balance': safe_float(row[15]),
            'unit_price': safe_float(row[16]),
            'amount': safe_float(row[17]),
            'special_instruction': s(row[18]) if len(row) > 18 else '',
            'item_group': s(row[19]) if len(row) > 19 else '',
            'unit_cost': safe_float(row[22]) if len(row) > 22 else 0.0,
            'cost': safe_float(row[23]) if len(row) > 23 else 0.0,
            'profit': safe_float(row[24]) if len(row) > 24 else 0.0,
            'diamond_weight': safe_float(row[25]) if len(row) > 25 else 0.0,
            'stone_weight': safe_float(row[26]) if len(row) > 26 else 0.0,
            'diverse_weight': safe_float(row[27]) if len(row) > 27 else 0.0,
            'metal_weight': safe_float(row[28]) if len(row) > 28 else 0.0,
            'currency': s(row[32]) if len(row) > 32 else 'US',
            'sequence': safe_int(row[34]) if len(row) > 34 else 0,
        }

        if d['amount'] and d['amount'] != 0:
            d['profit_pct'] = round(d['profit'] / d['amount'], 4)
        else:
            d['profit_pct'] = 0.0

        return d

    return row_to_doc_item


# ═══════════════════════════════════════════════════════
# Run all conversions
# ═══════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("SIS Data Conversion: raw BCP CSV → Odoo CSV")
    print("=" * 60)

    lookups = build_lookups()

    # --- SIS Party module ---
    raw_to_data(
        model_name='sis.region',
        csv_name='Regions.csv',
        fieldnames=['id', 'code', 'name'],
        row_to_dict=row_to_region,
        dest_folder=sis_party_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.country',
        csv_name='Countries.csv',
        fieldnames=['id', 'code', 'name', 'region_id'],
        row_to_dict=make_row_to_country(lookups),
        dest_folder=sis_party_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.pay.term',
        csv_name='PayTerms.csv',
        fieldnames=['id', 'name'],
        row_to_dict=row_to_pay_term,
        dest_folder=sis_party_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.shipper',
        csv_name='Shippers.csv',
        fieldnames=['id', 'name'],
        row_to_dict=row_to_shipper,
        dest_folder=sis_party_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.trade.fair',
        csv_name='TradeFairs.csv',
        fieldnames=['id', 'name', 'city', 'country_id', 'date_start', 'date_end'],
        row_to_dict=make_row_to_trade_fair(lookups),
        dest_folder=sis_party_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.party',
        csv_name='Customers.csv',
        fieldnames=['id', 'code', 'company', 'active', 'customer_rank', 'supplier_rank', 'contact_type', 'is_company',
                    'address', 'city', 'zip', 'country_id', 'phone', 'homepage', 'fax', 'email', 'notes',
                    'group_code', 'pay_term_id', 'ship_method_id', 'ship_stamp'],
        row_to_dict=make_row_to_party(lookups),
        dest_folder=sis_party_data,
        src_folder=backup_sis,
    )

    # --- SIS Document module ---
    raw_to_data(
        model_name='sis.doc.type',
        csv_name='DocTypes.csv',
        fieldnames=['id', 'code', 'name', 'category'],
        row_to_dict=row_to_doc_type,
        dest_folder=sis_doc_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.doc.in.mode',
        csv_name='DocInMode.csv',
        fieldnames=['id', 'name'],
        row_to_dict=row_to_doc_in_mode,
        dest_folder=sis_doc_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.document',
        csv_name='SalesDocs.csv',
        fieldnames=['id', 'name', 'doc_type_code', 'doc_type_id', 'legacy_id',
                    'date_created', 'date_due', 'party_id', 'party_code',
                    'margin_name', 'customer_po', 'closed', 'canceled',
                    'employee', 'currency', 'total_qty', 'total_cost',
                    'total_amount', 'total_fob', 'freight_insurance',
                    'total_cif', 'notes', 'footnotes'],
        row_to_dict=make_row_to_document(lookups),
        dest_folder=sis_doc_data,
        src_folder=backup_sis,
    )

    raw_to_data(
        model_name='sis.document.item',
        csv_name='SalesDocItems.csv',
        fieldnames=['id', 'document_id', 'design', 'ref_document', 'description',
                    'model_code', 'product_code', 'color_code', 'metal_code',
                    'purity', 'size_remarks', 'qty', 'qty_shipped', 'qty_balance',
                    'unit_price', 'amount', 'special_instruction', 'item_group',
                    'unit_cost', 'cost', 'profit', 'profit_pct',
                    'diamond_weight', 'stone_weight', 'diverse_weight', 'metal_weight',
                    'currency', 'sequence'],
        row_to_dict=make_row_to_doc_item(),
        dest_folder=sis_doc_data,
        src_folder=backup_sis,
    )

    print("\n" + "=" * 60)
    print("SIS Data Conversion Complete!")
    print("=" * 60)
