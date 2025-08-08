from odoo import fields, api, SUPERUSER_ID

def post_init_currency_setup(cr, registry=None):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # S'assurer que les devises sont actives
    for code in ['THB', 'USD', 'EUR']:
        currency = env['res.currency'].search([('name', '=', code)], limit=1)
        if currency:
            currency.active = True

    company = env.ref('base.main_company')
    company.write({
        'currency_provider': 'ecb',
        'currency_interval_unit': 'daily',
        'currency_next_execution_date': fields.Date.today(),
        'currency_id': env['res.currency'].search([('name', '=', 'THB')], limit=1).id,
    })

    # Import initial
    env['res.currency.rate.provider']._cron_fetch_currency_rates()
