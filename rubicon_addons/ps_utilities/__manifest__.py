{
    'name': 'PSUtilities',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Tools',
    'summary': 'PSUtilities — invoice design selection, product part updates, and Utilities master data',
    'depends': ['web', 'pdp_product', 'pdp_stone', 'sis_document'],
    'data': [
        'security/ir.model.access.csv',
        'data/pcs.ssp.csv',
        'views/utilities_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ps_utilities/static/src/js/ps_utilities.js',
            'ps_utilities/static/src/xml/ps_utilities.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
