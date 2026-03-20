"""
Fix res.partner records where city contains a state abbreviation (e.g. 'FL')
instead of a real city name.

Run via: docker compose exec odoo odoo shell -d rubicon --no-http < ops/setup/fix_partner_city_state.py

Logic:
  - For each partner with sis_code set (SIS parties)
  - If city is a 2-letter uppercase string AND state_id is empty
  - Look up the matching res.country.state by code + country
  - Set state_id and clear city
"""

partners = env['res.partner'].search([
    ('sis_code', '!=', False),
    ('city', '!=', False),
    ('state_id', '=', False),
])
print(f"Found {len(partners)} SIS partners with city set and state_id empty.")

fixed = 0
ambiguous = 0
skipped = 0

for p in partners:
    city_val = (p.city or '').strip()

    # Only process if city looks like a state code (2 uppercase letters)
    if not (len(city_val) == 2 and city_val.isupper()):
        skipped += 1
        continue

    domain = [('code', '=', city_val)]
    if p.country_id:
        domain.append(('country_id', '=', p.country_id.id))

    states = env['res.country.state'].search(domain)
    if len(states) == 1:
        p.write({'state_id': states.id, 'city': ''})
        fixed += 1
        print(f"  Fixed [{p.sis_code}] {p.name}: city='' state={states.name}")
    elif len(states) > 1:
        ambiguous += 1
        print(f"  Ambiguous [{p.sis_code}] {p.name}: city={city_val!r} matches {[s.name for s in states]}")
    else:
        skipped += 1

env.cr.commit()
print(f"\nDone: fixed={fixed}, ambiguous={ambiguous}, skipped={skipped}")
