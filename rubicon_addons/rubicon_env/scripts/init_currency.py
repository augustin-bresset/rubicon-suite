from odoo import api, SUPERUSER_ID

def run(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.currency'].load_missing_currencies()

    for code in ['THB', 'USD', 'EUR']:
        c = env['res.currency'].search([('name', '=', code)], limit=1)
        if c:
            c.active = True

    company = env.ref('base.main_company')
    company.write({
        'currency_provider': 'ecb',
        'currency_id': env.ref('base.THB').id,
        'currency_exchange_journal_id': env['account.journal'].search([], limit=1).id
    })
