{
    'name': 'PDP Base',
    'version': '1.0',
    'license': 'LGPL-3',
    'summary': 'Central configuration for PDP modules',
    'depends': ['rubicon_env'],
    'data': [
        'security/ir.model.access.csv',
        'data/pdp_config_data.xml',
        'views/pdp_config_views.xml',
        'views/pdp_config_menus.xml',
    ],
    'installable': True,
    'application': False,
}
