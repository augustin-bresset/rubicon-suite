{
    'name': 'PDP Alloy',
    'version': '1.0',
    'summary': 'Raw metals and alloy composition management',
    'category': 'PDP',
    'depends': ['rubicon_env'],
    'data': [
        'security/ir.model.access.csv',
        'views/alloy_menu.xml',
        'data/raw_metal_data.xml',
        'data/alloy_type_data.xml',
        'data/alloy_purity_data.xml',
        'data/alloy_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pdp_alloy/static/src/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
