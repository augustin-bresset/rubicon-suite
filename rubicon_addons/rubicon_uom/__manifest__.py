{
    'name': 'Rubicon UOM',
    'version': '0.1.0',
    'license': 'LGPL-3',
    'summary': 'Reusable unit-of-measure registry with ratio-based conversion and per-user preferences',
    'author': 'Rubicon',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/rubicon_uom_data.xml',
        'views/uom_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rubicon_uom/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
