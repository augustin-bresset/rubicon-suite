#!/usr/bin/env python3
"""
Clean party data via XML-RPC:
1. For companies: set `contact` = name of linked individual
2. For individuals: strip all fields except name — everything else is garbage overflow
3. Any stripped data with potential value goes to notes
"""
import re
import xmlrpc.client

URL = 'http://localhost:8069'
DB = 'rubicon'
USER = 'admin'
PASS = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def search_read(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASS, model, 'write', [ids, vals])

EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'^[\+\d][\d\s\-\(\)\.]{6,}$')

def is_valid_phone(val):
    if not val:
        return False
    return bool(PHONE_RE.match(val.strip()))

def is_valid_email(val):
    if not val:
        return False
    return bool(EMAIL_RE.search(val))

# =========================================================================
# 1. Clean individuals: strip garbage overflow
# =========================================================================
print("=== STEP 1: Cleaning individual rows ===")
indivs = search_read('sis.party', [('contact_type', '=', 'individual')],
    ['id', 'company', 'address', 'city', 'state', 'zip', 'country_id',
     'phone', 'fax', 'email', 'homepage', 'notes',
     'group_code', 'pay_term_id', 'ship_method_id',
     'ship_address', 'ship_city', 'ship_state', 'ship_zip',
     'ship_fedex_acc', 'ship_stamp',
     'bank_name', 'bank_address', 'bank_acc_name', 'bank_acc_no',
     'margin_id', 'account'])

cleaned = 0
for ind in indivs:
    vals = {}
    salvaged = []  # data worth keeping in notes

    # Strip ALL address fields — individuals don't have addresses
    for f in ['address', 'city', 'state', 'zip']:
        if ind[f]:
            salvaged.append(f"{f}={ind[f]}")
            vals[f] = False

    # Strip country — individuals inherit from parent company
    if ind['country_id']:
        vals['country_id'] = False

    # Validate phone — keep only if it looks like a real phone number
    if ind['phone'] and not is_valid_phone(ind['phone']):
        salvaged.append(f"phone={ind['phone']}")
        vals['phone'] = False

    # Validate fax
    if ind['fax'] and not is_valid_phone(ind['fax']):
        salvaged.append(f"fax={ind['fax']}")
        vals['fax'] = False

    # Validate email
    if ind['email'] and not is_valid_email(ind['email']):
        salvaged.append(f"email={ind['email']}")
        vals['email'] = False

    # Strip homepage — individuals rarely have one
    if ind['homepage']:
        salvaged.append(f"homepage={ind['homepage']}")
        vals['homepage'] = False

    # Strip all business fields — these belong to the company
    for f in ['group_code', 'account',
              'ship_address', 'ship_city', 'ship_state', 'ship_zip',
              'ship_fedex_acc', 'ship_stamp',
              'bank_name', 'bank_address', 'bank_acc_name', 'bank_acc_no']:
        if ind[f]:
            vals[f] = False

    # Clear Many2one fields
    if ind['margin_id']:
        vals['margin_id'] = False
    if ind['pay_term_id']:
        vals['pay_term_id'] = False
    if ind['ship_method_id']:
        vals['ship_method_id'] = False

    # Save salvaged data to notes if there was anything meaningful
    if salvaged:
        existing_notes = ind['notes'] or ''
        note_line = "Original overflow: " + " | ".join(salvaged)
        if existing_notes:
            vals['notes'] = existing_notes + "\n" + note_line
        else:
            vals['notes'] = note_line

    if vals:
        write('sis.party', [ind['id']], vals)
        cleaned += 1

print(f"  Cleaned {cleaned}/{len(indivs)} individuals")

# =========================================================================
# 2. Populate contact field on companies from linked individual
# =========================================================================
print("\n=== STEP 2: Populating contact field on companies ===")
companies = search_read('sis.party', [('contact_type', '=', 'company')],
    ['id', 'company', 'code', 'contact', 'child_ids'])

contact_set = 0
for comp in companies:
    if comp['child_ids']:
        # Get the first (usually only) contact person
        contacts = search_read('sis.party', [('id', 'in', comp['child_ids'])],
                               ['company'])  # 'company' field = person's name
        if contacts:
            contact_name = contacts[0]['company']
            if not comp['contact'] or comp['contact'] != contact_name:
                write('sis.party', [comp['id']], {'contact': contact_name})
                contact_set += 1

print(f"  Set contact on {contact_set}/{len(companies)} companies")

# =========================================================================
print(f"\n[SUCCESS] Done! Cleaned {cleaned} individuals, set {contact_set} company contacts")
