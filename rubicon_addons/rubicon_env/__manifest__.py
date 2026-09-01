{
    'name': 'Rubicon - Environment Init',
    'summary': 'Environment initializer: currencies, company, access levels and roles',
    'version': '18.0.1.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        # currency_rate_update is optional — can be installed separately in production
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