{
    'name': 'Rubicon - Environment Init',
    'summary': 'Environment initilizer: currencies, rates, cron, etc.',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'currency_rate_update',
        
        ],
    'data': [
        'data/res_currency.xml',
        'data/res_company.xml',
        'security/security.xml',
        ],

    # 'post_init_hook': 'post_init_currency_setup',
    
    'installable': True,
    'auto_install': False,
}