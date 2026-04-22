"""
Convert raw SIS BCP CSV exports into Odoo-ready CSV format.

Source: data/backup_sis/*.csv (headerless BCP export)
Target: rubicon_addons/sis_party/data/*.csv and rubicon_addons/sis_document/data/*.csv

Usage: python3 -m rubicon_import.raw_to_data.raw_to_data_sis
"""

import os
import sys
import csv
import re

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
    """Keep digits, spaces, + and - (readable format); strip null bytes and leading/trailing space."""
    v = s(val)
    if not v:
        return ''
    v = re.sub(r'[^\d +\-()]', '', v)
    return v.strip()

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

# Maps SIS country codes (Countries.csv col 0) → Odoo res.country names
_SIS_TO_ODOO_COUNTRY = {
    'AE': 'United Arab Emirates',
    'AR': 'Argentina',
    'AU': 'Australia',
    'BE': 'Belgium',
    'BT': 'Saint Barthélemy',
    'BZ': 'Brazil',
    'CA': 'Canada',
    'CB': 'Colombia',
    'CH': 'Chile',
    'CN': 'China',
    'CO': 'Costa Rica',
    'EG': 'Egypt',
    'EN': 'United Kingdom',
    'FR': 'France',
    'GM': 'Germany',
    'GR': 'Greece',
    'HD': 'Honduras',
    'HK': 'Hong Kong',
    'HO': 'Netherlands',
    'IN': 'Indonesia',
    'IS': 'Israel',
    'IT': 'Italy',
    'JP': 'Japan',
    'KR': 'South Korea',
    'ME': 'Mexico',
    'ML': 'Malaysia',
    'NC': 'New Caledonia',
    'NL': 'Netherlands',
    'NZ': 'New Zealand',
    'RU': 'Russia',
    'SA': 'South Africa',
    'SG': 'Singapore',
    'SP': 'Spain',
    'SU': 'Saudi Arabia',
    'SW': 'Switzerland',
    'TA': 'Tanzania, United Republic of',
    'TH': 'Thailand',
    'TU': 'Turkey',
    'TW': 'Taiwan',
    'UK': 'Ukraine',
    'US': 'United States',
    'VE': 'Venezuela',
}


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
            'country_id': _SIS_TO_ODOO_COUNTRY.get(country_code, ''),
            'date_start': date_start,
            'date_end': date_end,
        }
    return row_to_trade_fair


_RECORD_RE = re.compile(r'^(\d+),')

_DIAMOND_BOILERPLATE = (
    'The seller hereby guarantees that these diamonds are "conflict-free" and confirms\n'
    'its adherence to compliance with the SoW guidelines of the WDC "\n'
    '- "The diamonds here invoiced are exclusively of natural origin and untreated, on the\n'
    'basis of personal knowledge and / or written guarantees provided by the supplier of\n'
    'these diamonds"'
)


def preprocess_customers(src_path, dst_path):
    """
    Join multi-line BCP Customers.csv records into single lines.

    The MSSQL BCP export embeds literal newlines in text fields without quoting,
    so csv.reader splits each physical line as a separate row. Each logical record
    starts with a monotonically-increasing integer ID. We detect record boundaries
    by that ID and join the physical lines, then strip the diamond boilerplate that
    appears verbatim in every notes field.
    """
    with open(src_path, encoding='utf-8') as f:
        raw = f.readlines()

    records = []
    cur = []
    last_id = -1
    for line in raw:
        m = _RECORD_RE.match(line)
        if m:
            pid = int(m.group(1))
            if pid > last_id:
                if cur:
                    records.append(''.join(cur))
                cur = [line]
                last_id = pid
                continue
        cur.append(line)
    if cur:
        records.append(''.join(cur))

    with open(dst_path, 'w', encoding='utf-8', newline='') as f:
        for rec in records:
            cleaned = rec.replace(_DIAMOND_BOILERPLATE, '')
            cleaned = cleaned.replace('\x00', '')
            cleaned = cleaned.replace('\n', ' ').replace('\r', '').strip()
            f.write(cleaned + '\n')

    print(f"[INFO] preprocess_customers: {len(records)} records → {dst_path}")
    return dst_path


def make_row_to_party(lookups):
    # Build country_name → code lookup for anchor detection
    country_name_to_code = {}
    with open(os.path.join(backup_sis, 'Countries.csv'), encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                country_name_to_code[row[1].strip().upper()] = row[0].strip()
    country_names = set(country_name_to_code.keys())
    country_codes = set(lookups['country'].keys())

    def _find_cc_col(tokens):
        """
        Locate the country_code column using the full country_name as an anchor.
        country_code is always 4 columns after the country_name (city, state, zip, cc).
        Falls back to a direct scan from col 10 for records with missing/null country_name.
        """
        for i, t in enumerate(tokens):
            if t.strip().upper() in country_names:
                cc = i + 4
                if cc < len(tokens) and tokens[cc].strip() in country_codes:
                    return cc
        for i in range(10, min(len(tokens), 35)):
            if tokens[i].strip() in country_codes:
                return i
        return None

    def _get(tokens, col, default=''):
        if col is None or col < 0 or col >= len(tokens):
            return default
        return s(tokens[col])

    def row_to_party(row):
        if len(row) < 4:
            return None
        pid = s(row[0])
        code = s(row[1])
        company = s(row[2])
        if not pid or not company:
            return None
        try:
            int(pid)
        except ValueError:
            return None  # skip garbage rows from bad joins

        is_company = bool(code and code != '0')
        cc_col = _find_cc_col(row)

        if cc_col is not None:
            city        = _get(row, cc_col - 3)
            zip_code    = _get(row, cc_col - 1)
            country_cc  = _get(row, cc_col)
            phone_col        = cc_col + 1
            fax_col          = cc_col + 3
            email_col        = cc_col + 4
            notes1_col       = cc_col + 5
            group_col        = cc_col + 7
            pay_term_col     = cc_col + 8
            ship_method_col  = cc_col + 9
            notes2_col       = cc_col + 12
            inactive_col     = cc_col + 13
            contact_name_col = cc_col + 14
            customer_col     = cc_col + 16
            vendor_col       = cc_col + 17
        else:
            city = zip_code = country_cc = ''
            phone_col = fax_col = email_col = notes1_col = None
            group_col = pay_term_col = ship_method_col = None
            notes2_col = inactive_col = contact_name_col = None
            customer_col = vendor_col = None

        pay_term    = _get(row, pay_term_col)
        ship_method = _get(row, ship_method_col)

        notes1 = _get(row, notes1_col).strip()
        notes2 = _get(row, notes2_col).strip()
        notes = ' | '.join(filter(None, [notes1, notes2]))

        inactive_bit = _get(row, inactive_col) == '1'
        customer_bit = _get(row, customer_col) == '1'
        vendor_bit   = _get(row, vendor_col)   == '1'

        contact_name = _get(row, contact_name_col).strip() if contact_name_col else ''

        # Email: strip "mailto:" prefix if present
        email_raw = _get(row, email_col)
        email = re.sub(r'^mailto:', '', email_raw, flags=re.IGNORECASE).strip()

        # Margin: stored as pdp.margin code (_rec_name='code'), e.g. "WHO" = Wholesale
        margin_code = _get(row, group_col).strip() if group_col else ''

        # Ship address: find second country occurrence after the company block.
        # The country NAME is the anchor (city, state, zip, cc follow at +1..+4).
        # fedex_acc is the second-to-last field; stamp is always row[-1].
        ship_city = ship_zip = ship_cc = ship_state = ''
        _scc = None
        if cc_col is not None:
            search_from = (contact_name_col if contact_name_col is not None else cc_col + 14) + 3
            for i in range(search_from, min(len(row), 70)):
                if row[i].strip().upper() in country_names:
                    scc = i + 4
                    if scc < len(row) and row[scc].strip() in country_codes:
                        _scc = scc
                        ship_city  = _get(row, scc - 3)
                        ship_state = _get(row, scc - 2).strip()
                        ship_zip   = _get(row, scc - 1)
                        ship_cc    = _get(row, scc)
                        break
        fedex_acc = s(row[-2]) if len(row) >= 2 else ''

        # Ship address lines: slots cc_col+18..21, minus city/zip text that spills in.
        # e.g. A&J  → ['KLEX CORPORATION', '7905 S.W. 86 Street', '', 'Suite 601']
        #      EMASUR → ["L'ACHEMINEUR...", 'ZI LES...', 'AULNAY SOUS BOIS', '93605']
        # We strip out the structured city/zip values so only real address lines remain.
        if cc_col is not None:
            city_norm = ship_city.strip().upper()
            zip_norm  = ship_zip.strip()
            ship_addr_slots = [
                _get(row, cc_col + 18 + i).strip()
                for i in range(4)
                if cc_col + 18 + i < len(row)
            ]
            ship_addr_lines = [
                v for v in ship_addr_slots
                if v and v.upper() != city_norm and v.strip() != zip_norm
            ]
            ship_street2 = ship_addr_lines[0] if ship_addr_lines else ''
            ship_street  = ' '.join(ship_addr_lines[1:]) if len(ship_addr_lines) > 1 else ''
        else:
            ship_street = ship_street2 = ''

        # Bank info: scc+1..scc+7 when scc+1 is non-empty (skip parties with no bank)
        bank_name = bank_address = bank_acc_name = bank_acc_no = ''
        if _scc is not None and _get(row, _scc + 1):
            bank_name = _get(row, _scc + 1)
            addr_parts = [_get(row, _scc + j) for j in range(2, 6)]
            bank_address = '\n'.join(p.strip() for p in addr_parts if p.strip())
            bank_acc_name = _get(row, _scc + 6)
            bank_acc_no = _get(row, _scc + 7)

        yield {
            'id': f'sis_party_{pid}',
            'sis_code': code,
            'name': company,
            'active': not inactive_bit,
            'customer_rank': 1 if customer_bit else 0,
            'supplier_rank': 1 if vendor_bit else 0,
            'is_company': is_company,
            'street': _get(row, 5),
            'street2': _get(row, 4),
            'city': city,
            'state_code': _get(row, cc_col - 2).strip() if cc_col is not None else '',
            'zip': zip_code,
            'country_id': _SIS_TO_ODOO_COUNTRY.get(country_cc, '') if country_cc else '',
            'phone': clean_phone(_get(row, phone_col)),
            'mobile': clean_phone(_get(row, cc_col + 2)) if cc_col is not None else '',
            'email': email,
            'website': '',
            'notes': notes,
            'sis_is_customer': customer_bit,
            'sis_is_vendor': vendor_bit,
            'sis_contact': contact_name,
            'margin_id': margin_code,
            'sis_pay_term_id': lookups['payterm'].get(pay_term, ''),
            'sis_ship_method_id': lookups['shipper'].get(ship_method, ''),
            'sis_ship_fedex_acc': fedex_acc,
            'sis_ship_street': ship_street,
            'sis_ship_street2': ship_street2,
            'sis_ship_city': ship_city,
            'sis_ship_state_code': ship_state,
            'sis_ship_zip': ship_zip,
            'sis_ship_country_id': _SIS_TO_ODOO_COUNTRY.get(ship_cc, '') if ship_cc else '',
            'sis_ship_stamp': s(row[-1]) if row else '',
            'bank_name': bank_name,
            'bank_address': bank_address,
            'bank_acc_name': bank_acc_name,
            'bank_acc_no': bank_acc_no,
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

    customers_joined = os.path.join(backup_sis, 'CustomersJoined.csv')
    preprocess_customers(
        src_path=os.path.join(backup_sis, 'Customers.csv'),
        dst_path=customers_joined,
    )
    raw_to_data(
        model_name='sis.party',
        csv_name='CustomersJoined.csv',
        fieldnames=['id', 'sis_code', 'name', 'active', 'customer_rank', 'supplier_rank',
                    'is_company', 'street', 'street2',
                    'city', 'state_code', 'zip', 'country_id',
                    'phone', 'mobile', 'email', 'website', 'notes',
                    'sis_is_customer', 'sis_is_vendor', 'sis_contact',
                    'margin_id', 'sis_pay_term_id', 'sis_ship_method_id',
                    'sis_ship_fedex_acc',
                    'sis_ship_street', 'sis_ship_street2',
                    'sis_ship_city', 'sis_ship_state_code', 'sis_ship_zip',
                    'sis_ship_country_id', 'sis_ship_stamp',
                    'bank_name', 'bank_address', 'bank_acc_name', 'bank_acc_no'],
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
