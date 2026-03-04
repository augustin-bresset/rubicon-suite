#!/usr/bin/env python3
"""Reset admin password, set company logo, and clear asset cache."""
import base64
import sys
import odoo
from odoo import api, SUPERUSER_ID

# Initialize Odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'rubicon', '--no-http'])
odoo.service.server.start(preload=[], stop=True)
registry = odoo.registry('rubicon')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Reset admin password
    admin = env['res.users'].search([('login', '=', 'admin')], limit=1)
    if admin:
        admin.password = 'admin'
        print(f"[OK] Admin password reset for user ID {admin.id}")
    else:
        print("[WARN] No admin user found")

    # 2. Set company logo from /mnt/extra-addons/../logo.webp
    # The file is mounted at /mnt/extra-addons relative to addons
    import os
    logo_path = '/tmp/logo.webp'
    if not os.path.exists(logo_path):
        print(f"[WARN] Logo not found at {logo_path}")
    else:
        with open(logo_path, 'rb') as f:
            logo_data = base64.b64encode(f.read())
        company = env['res.company'].search([], limit=1)
        if company:
            company.logo = logo_data
            print(f"[OK] Logo set for company: {company.name}")

    # 3. Clear asset cache
    assets = env['ir.attachment'].search([
        ('name', 'like', 'web.assets_%'),
    ])
    if assets:
        count = len(assets)
        assets.unlink()
        print(f"[OK] Cleared {count} cached asset bundles")
    else:
        print("[INFO] No cached asset bundles found")

    cr.commit()
    print("[DONE] All changes committed")
