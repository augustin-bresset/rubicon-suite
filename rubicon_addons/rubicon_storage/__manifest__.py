{
    'name': 'Rubicon Storage',
    'version': '1.0',
    'license': 'LGPL-3',
    'summary': 'Stone list from Sale Orders',
    'depends': ['web', 'pdp_product', 'sis_document', 'sis_frontend'],
    'data': [
        'report/report_action.xml',
        'report/report_stone_list.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rubicon_storage/static/src/js/rubicon_storage.js',
            'rubicon_storage/static/src/xml/rubicon_storage.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
