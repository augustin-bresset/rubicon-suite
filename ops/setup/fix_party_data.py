#!/usr/bin/env python3
"""
Fix sis.party.csv: validate fields, link individuals to companies, fix IDs.

Outputs:
  - rubicon_addons/sis_party/data/sis.party.csv  (cleaned)
  - fix_party_report.txt                          (change log)
"""
import csv
import re
import os
import sys
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE, "rubicon_addons/sis_party/data/sis.party.csv")
COUNTRY_CSV = os.path.join(BASE, "rubicon_addons/sis_party/data/sis.country.csv")
OUTPUT_CSV = INPUT_CSV  # overwrite in-place
REPORT_FILE = os.path.join(BASE, "fix_party_report.txt")

# ---------------------------------------------------------------------------
# Load country lookup
# ---------------------------------------------------------------------------
def load_countries(path):
    """Return {name_upper: xml_id, code_upper: xml_id} mapping."""
    lookup = {}
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            xml_id = row['id'].strip()
            code = row['code'].strip().upper()
            name = row['name'].strip().upper()
            lookup[code] = xml_id
            lookup[name] = xml_id
            # Common aliases
            if name == 'UNITED STATES OF AMERICA':
                lookup['US'] = xml_id
                lookup['USA'] = xml_id
                lookup['UNITED STATES'] = xml_id
            if name == 'UNITED KINGDOM':
                lookup['UK'] = xml_id
                lookup['ENGLAND'] = xml_id
                lookup['GREAT BRITAIN'] = xml_id
            if code == 'NL':
                lookup['NETHERLAND'] = xml_id
                lookup['NETHERLANDS'] = xml_id
                lookup['HOLLAND'] = xml_id
            if code == 'NZ':
                lookup['NEW ZELAND'] = xml_id
                lookup['NEW ZEALAND'] = xml_id
    return lookup

# ---------------------------------------------------------------------------
# Field detection heuristics
# ---------------------------------------------------------------------------
COUNTRY_LOOKUP = {}  # populated in main

def is_country(val):
    """Check if value looks like a country name or code."""
    if not val:
        return False
    v = val.strip().upper()
    return v in COUNTRY_LOOKUP

def resolve_country(val):
    """Return sis.country XML ID for a country value, or None."""
    if not val:
        return None
    v = val.strip().upper()
    return COUNTRY_LOOKUP.get(v)

# Common 2-letter US state codes
US_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
    'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
    'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
    'TX','UT','VT','VA','WA','WV','WI','WY','DC',
    # Australian states
    'NSW','VIC','QLD','SA','WA','TAS','NT','ACT',
    # Common abbreviations
    'N.Y.','N.J.','N.Y.C.','MISSOURI','ARKANSAS','VIRGINIA','CALIFONIA',
    'CALIFORNIA','MARYLAND','HAWAII','TENNESSEE',
}

PHONE_RE = re.compile(
    r'^[\s]*[\+]?[\d\s\-\(\)\.]{7,}$'
)

EMAIL_RE = re.compile(
    r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
)

URL_RE = re.compile(
    r'(https?://|www\.)',
    re.IGNORECASE
)

ZIP_RE = re.compile(
    r'^[\d\-\s]{3,10}$|^\d{5}$|^\d{4,5}[\-]\d{4}$|^[A-Z]\d[A-Z]\s?\d[A-Z]\d$',
    re.IGNORECASE
)

def looks_like_phone(val):
    if not val:
        return False
    # Must have at least 7 digits
    digits = re.sub(r'\D', '', val)
    return len(digits) >= 7 and PHONE_RE.match(val) is not None

def looks_like_email(val):
    if not val:
        return False
    return EMAIL_RE.search(val) is not None

def looks_like_url(val):
    if not val:
        return False
    return URL_RE.search(val) is not None

def looks_like_zip(val):
    if not val:
        return False
    v = val.strip()
    # Short values that are numeric or alphanumeric postal codes
    return len(v) <= 12 and ZIP_RE.match(v) is not None

def is_us_state(val):
    if not val:
        return False
    return val.strip().upper() in US_STATES or val.strip() in US_STATES

# ---------------------------------------------------------------------------
# Fix a single company row
# ---------------------------------------------------------------------------
def fix_company_row(row, changes):
    """Detect and fix mis-assigned fields in a company row. Returns modified row."""
    row_id = row.get('id', '?')

    # --- Country resolution ---
    # Check if country_id is already an XML ID
    country_val = row.get('country_id', '').strip()
    if country_val and not country_val.startswith('sis_country_'):
        resolved = resolve_country(country_val)
        if resolved:
            changes.append(f"  [{row_id}] country_id: '{country_val}' → '{resolved}'")
            row['country_id'] = resolved

    # Check city, state, zip for country names that should be in country_id
    for field in ['city', 'state', 'zip']:
        val = row.get(field, '').strip()
        if val and is_country(val) and not row.get('country_id'):
            resolved = resolve_country(val)
            if resolved:
                changes.append(f"  [{row_id}] MOVE {field}='{val}' → country_id='{resolved}'")
                row['country_id'] = resolved
                row[field] = ''

    # Check if address columns have zip-like values in wrong place
    # e.g., zip in city, state code in zip
    city_val = row.get('city', '').strip()
    state_val = row.get('state', '').strip()
    zip_val = row.get('zip', '').strip()

    # If zip is a country code (2 letters matching a country), move it
    if zip_val and len(zip_val) <= 3 and is_country(zip_val) and not row.get('country_id'):
        resolved = resolve_country(zip_val)
        if resolved:
            changes.append(f"  [{row_id}] MOVE zip='{zip_val}' → country_id='{resolved}'")
            row['country_id'] = resolved
            row['zip'] = ''

    # If state is a country name
    if state_val and is_country(state_val) and not is_us_state(state_val):
        if not row.get('country_id') or row['country_id'] == '':
            resolved = resolve_country(state_val)
            if resolved:
                changes.append(f"  [{row_id}] MOVE state='{state_val}' → country_id='{resolved}'")
                row['country_id'] = resolved
                row['state'] = ''

    # --- Communication fields ---
    # Check if homepage has email
    homepage_val = row.get('homepage', '').strip()
    if homepage_val and looks_like_email(homepage_val) and not looks_like_url(homepage_val):
        if not row.get('email'):
            changes.append(f"  [{row_id}] MOVE homepage → email: '{homepage_val}'")
            row['email'] = homepage_val
            row['homepage'] = ''

    # Check if email has URL
    email_val = row.get('email', '').strip()
    if email_val and looks_like_url(email_val) and not looks_like_email(email_val):
        if not row.get('homepage'):
            changes.append(f"  [{row_id}] MOVE email → homepage: '{email_val}'")
            row['homepage'] = email_val
            row['email'] = ''

    # Strip "mailto:" prefix from emails
    email_val = row.get('email', '').strip()
    if email_val and email_val.lower().startswith('mailto:'):
        cleaned = email_val[7:].strip()
        changes.append(f"  [{row_id}] CLEAN email: strip 'mailto:' prefix")
        row['email'] = cleaned

    return row

# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------
def main():
    global COUNTRY_LOOKUP

    print(f"Loading countries from {COUNTRY_CSV}...")
    COUNTRY_LOOKUP = load_countries(COUNTRY_CSV)
    print(f"  {len(COUNTRY_LOOKUP)} lookup entries")

    print(f"Reading parties from {INPUT_CSV}...")
    rows = []
    with open(INPUT_CSV, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(OrderedDict(row))

    print(f"  {len(rows)} rows loaded")

    changes = []
    output_rows = []
    last_company_id = None
    company_count = 0
    individual_count = 0
    fixed_id_count = 0

    # Add parent_id to fieldnames if not present
    if 'parent_id' not in fieldnames:
        # Insert after 'is_company'
        idx = fieldnames.index('is_company') + 1 if 'is_company' in fieldnames else len(fieldnames)
        fieldnames = list(fieldnames)
        fieldnames.insert(idx, 'parent_id')

    for i, row in enumerate(rows):
        contact_type = row.get('contact_type', '').strip()
        row_id = row.get('id', '').strip()

        if contact_type == 'company':
            company_count += 1
            last_company_id = row_id
            row['parent_id'] = ''

            # Fix company fields
            row = fix_company_row(row, changes)
            output_rows.append(row)

        elif contact_type == 'individual':
            individual_count += 1

            # Fix broken XML IDs
            if 'these diamonds' in row_id or not row_id or row_id == '0':
                if last_company_id:
                    new_id = f"{last_company_id}_contact"
                else:
                    new_id = f"sis_party_individual_{i}"
                changes.append(f"  FIX ID: '{row_id}' → '{new_id}'")
                row['id'] = new_id
                fixed_id_count += 1

            # Link to parent company
            if last_company_id:
                row['parent_id'] = last_company_id
                # Don't log every link, just count
            else:
                row['parent_id'] = ''

            # Individuals often have '1' or empty in address — clean it
            addr = row.get('address', '').strip()
            if addr == '1' or addr == '0':
                row['address'] = ''

            output_rows.append(row)
        else:
            # Unknown type, keep as-is
            row['parent_id'] = row.get('parent_id', '')
            output_rows.append(row)

    # --- Write output ---
    print(f"\nWriting cleaned CSV to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in output_rows:
            # Ensure all fieldnames have a value
            for fn in fieldnames:
                if fn not in row:
                    row[fn] = ''
            writer.writerow(row)

    # --- Write report ---
    print(f"Writing report to {REPORT_FILE}...")
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("SIS Party Data Fix Report\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total rows processed: {len(rows)}\n")
        f.write(f"Companies: {company_count}\n")
        f.write(f"Individuals: {individual_count}\n")
        f.write(f"Fixed IDs: {fixed_id_count}\n")
        f.write(f"Field changes: {len(changes)}\n\n")
        f.write("-" * 70 + "\n")
        f.write("CHANGES\n")
        f.write("-" * 70 + "\n")
        for c in changes:
            f.write(c + "\n")
        f.write("\n[DONE]\n")

    print(f"\n✅ Done!")
    print(f"   Companies:     {company_count}")
    print(f"   Individuals:   {individual_count}")
    print(f"   Fixed IDs:     {fixed_id_count}")
    print(f"   Field changes: {len(changes)}")
    print(f"   Report:        {REPORT_FILE}")

if __name__ == '__main__':
    main()
