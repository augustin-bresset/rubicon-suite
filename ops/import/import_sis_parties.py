"""
In-process SIS party loader: sis.party.csv -> res.partner (+ bank + children).

Run via odoo shell (env is provided):
    docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/import/import_sis_parties.py

For each company row in the CSV it upserts (keyed by sis_code, idempotent):
  - the company res.partner (address/contact/SIS fields, country by name,
    state by code, margin by code, pay term & shipper by name);
  - a res.partner.bank from the bank_* columns;
  - a type='delivery' child from the sis_ship_* address columns;
  - a type='contact' child from sis_contact.

These are exactly the shapes the SIS workspace reads (bank_ids, delivery/contact
children, state_id). Replaces import_parties_odoo + sync_parties + populate_parties
+ migrate_to_partner; no XML-RPC.
"""
import csv
import re

CSV_PATH = '/mnt/extra-addons/sis_party/data/sis.party.csv'
EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}')

Partner = env['res.partner']
Bank = env['res.partner.bank']

# ── Lookup tables ──────────────────────────────────────────────────────────
print("Loading lookup tables...")
country_by_name = {c.name.upper(): c.id for c in env['res.country'].search([])}
state_by_country_code = {
    (s.country_id.id, (s.code or '').upper()): s.id
    for s in env['res.country.state'].search([])
}
pay_term_by_name = {p.name: p.id for p in env['sis.pay.term'].search([])}
shipper_by_name = {s.name: s.id for s in env['sis.shipper'].search([])}
margin_by_code = {m.code: m.id for m in env['pdp.margin'].search([])}


def resolve_country(name):
    return country_by_name.get((name or '').strip().upper())


def resolve_state(state_code, country_id):
    if not state_code or not country_id:
        return None
    return state_by_country_code.get((country_id, state_code.strip().upper()))


# ── Existing records (idempotent upsert) ───────────────────────────────────
print("Loading existing SIS partners / children / banks...")
partner_by_code = {
    p.sis_code: p.id
    for p in Partner.search([('sis_code', '!=', False), ('is_company', '=', True)])
}
children = Partner.search([
    ('type', 'in', ['delivery', 'contact']),
    ('parent_id', 'in', list(partner_by_code.values())),
])
delivery_by_parent, contact_by_parent = {}, {}
for c in children:
    if c.type == 'delivery':
        delivery_by_parent.setdefault(c.parent_id.id, c.id)
    else:
        contact_by_parent.setdefault(c.parent_id.id, c.id)
bank_by_partner = {
    b.partner_id.id: b.id
    for b in Bank.search([('partner_id', 'in', list(partner_by_code.values()))])
}
print(f"  {len(partner_by_code)} companies, "
      f"{len(delivery_by_parent)} delivery, {len(contact_by_parent)} contacts, "
      f"{len(bank_by_partner)} banks")

# ── Read CSV ───────────────────────────────────────────────────────────────
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
print(f"Read {len(rows)} CSV rows from {CSV_PATH}")

# ── Upsert ─────────────────────────────────────────────────────────────────
created = updated = skipped = banks = deliveries = contacts = 0

for row in rows:
    code = row.get('sis_code', '').strip()
    if not code or row.get('is_company', '').strip() != 'True':
        skipped += 1
        continue

    company_name = row.get('name', '').strip()
    if not company_name:
        skipped += 1
        continue

    vals = {
        'name': company_name,
        'sis_code': code,
        'company_type': 'company',
        'active': row.get('active', '').strip() != 'False',
        'sis_is_customer': row.get('sis_is_customer', '').strip() == 'True',
        'sis_is_vendor': row.get('sis_is_vendor', '').strip() == 'True',
    }
    # customer_rank / supplier_rank only exist when sale/purchase are installed.
    for fld in ('customer_rank', 'supplier_rank'):
        if fld not in Partner._fields:
            continue
        raw = row.get(fld, '').strip()
        if raw:
            try:
                vals[fld] = int(float(raw))
            except ValueError:
                pass

    # Address
    for fld in ('street', 'street2', 'city', 'zip'):
        v = row.get(fld, '').strip()
        if v and v not in ('NA', '0', '1'):
            vals[fld] = v
    country_id = resolve_country(row.get('country_id', ''))
    if country_id:
        vals['country_id'] = country_id
    state_id = resolve_state(row.get('state_code', ''), country_id)
    if state_id:
        vals['state_id'] = state_id

    # Contact
    phone = row.get('phone', '').strip()
    if phone:
        vals['phone'] = phone
    mobile = row.get('mobile', '').strip()
    if mobile:
        vals['mobile'] = mobile
    email = row.get('email', '').strip()
    if email and EMAIL_RE.search(email):
        vals['email'] = email
    website = row.get('website', '').strip()
    if website:
        vals['website'] = website
    notes = row.get('notes', '').strip()
    if notes:
        vals['comment'] = notes

    # SIS defaults
    margin_code = row.get('margin_id', '').strip()
    if margin_code in margin_by_code:
        vals['margin_id'] = margin_by_code[margin_code]
    pay_term = row.get('sis_pay_term_id', '').strip()
    if pay_term in pay_term_by_name:
        vals['sis_pay_term_id'] = pay_term_by_name[pay_term]
    ship_method = row.get('sis_ship_method_id', '').strip()
    if ship_method in shipper_by_name:
        vals['sis_ship_method_id'] = shipper_by_name[ship_method]
    fedex = row.get('sis_ship_fedex_acc', '').strip()
    if fedex:
        vals['sis_ship_fedex_acc'] = fedex
    stamp = row.get('sis_ship_stamp', '').strip()
    if stamp:
        vals['sis_ship_stamp'] = stamp

    # Upsert company
    partner_id = partner_by_code.get(code)
    if partner_id:
        Partner.browse(partner_id).write(vals)
        updated += 1
    else:
        partner_id = Partner.create(vals).id
        partner_by_code[code] = partner_id
        created += 1

    # Bank
    bank_acc_no = row.get('bank_acc_no', '').strip()
    bank_name = row.get('bank_name', '').strip()
    if bank_acc_no or bank_name:
        bank_vals = {
            'partner_id': partner_id,
            'acc_number': bank_acc_no or '—',
            'acc_holder_name': row.get('bank_acc_name', '').strip(),
            'sis_bank_name': bank_name,
            'sis_bank_address': row.get('bank_address', '').strip(),
        }
        existing = bank_by_partner.get(partner_id)
        if existing:
            Bank.browse(existing).write(bank_vals)
        else:
            bank_by_partner[partner_id] = Bank.create(bank_vals).id
            banks += 1

    # Delivery child
    ship_country_id = resolve_country(row.get('sis_ship_country_id', ''))
    ship_city = row.get('sis_ship_city', '').strip()
    ship_street = row.get('sis_ship_street', '').strip()
    if ship_city or ship_country_id or ship_street:
        delivery_vals = {
            'type': 'delivery',
            'parent_id': partner_id,
            'name': row.get('sis_ship_name', '').strip() or company_name,
        }
        if ship_street:
            delivery_vals['street'] = ship_street
        ship_street2 = row.get('sis_ship_street2', '').strip()
        if ship_street2:
            delivery_vals['street2'] = ship_street2
        if ship_city:
            delivery_vals['city'] = ship_city
        ship_zip = row.get('sis_ship_zip', '').strip()
        if ship_zip:
            delivery_vals['zip'] = ship_zip
        if ship_country_id:
            delivery_vals['country_id'] = ship_country_id
        ship_state_id = resolve_state(row.get('sis_ship_state_code', ''), ship_country_id)
        if ship_state_id:
            delivery_vals['state_id'] = ship_state_id
        existing = delivery_by_parent.get(partner_id)
        if existing:
            Partner.browse(existing).write(delivery_vals)
        else:
            delivery_by_parent[partner_id] = Partner.create(delivery_vals).id
            deliveries += 1

    # Contact child
    contact_name = row.get('sis_contact', '').strip()
    if contact_name:
        contact_vals = {
            'type': 'contact', 'parent_id': partner_id,
            'name': contact_name, 'is_company': False,
        }
        existing = contact_by_parent.get(partner_id)
        if existing:
            Partner.browse(existing).write(contact_vals)
        else:
            contact_by_parent[partner_id] = Partner.create(contact_vals).id
            contacts += 1

env.cr.commit()

print("\n=== SIS parties loaded ===")
print(f"  companies : created={created} updated={updated} skipped={skipped}")
print(f"  banks created     : {banks}")
print(f"  delivery created  : {deliveries}")
print(f"  contacts created  : {contacts}")
total = Partner.search_count([('sis_code', '!=', False), ('is_company', '=', True)])
print(f"  total SIS companies in DB: {total}")
