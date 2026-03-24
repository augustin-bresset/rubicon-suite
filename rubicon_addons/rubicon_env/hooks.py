from odoo import fields, api, SUPERUSER_ID

def post_init_currency_setup(cr, registry=None):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # S'assurer que les devises sont actives
    for code in ['THB', 'USD', 'EUR']:
        currency = env['res.currency'].search([('name', '=', code)], limit=1)
        if currency:
            currency.active = True

    # Devise principale de la company : THB
    thb = env['res.currency'].search([('name', '=', 'THB')], limit=1)
    if thb:
        company = env.ref('base.main_company')
        company.write({'currency_id': thb.id})

    # Fonctionnalités currency_rate_update (optionnel — module OCA)
    cru_installed = env['ir.module.module'].search([
        ('name', '=', 'currency_rate_update'),
        ('state', '=', 'installed'),
    ], limit=1)
    if cru_installed:
        company = env.ref('base.main_company')
        company.write({
            'currency_provider': 'ecb',
            'currency_interval_unit': 'daily',
            'currency_next_execution_date': fields.Date.today(),
        })
        env['res.currency.rate.provider']._cron_fetch_currency_rates()
