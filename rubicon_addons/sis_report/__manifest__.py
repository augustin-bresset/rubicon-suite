{
    'name': 'SIS Report',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Sales',
    'summary': 'SIS Report — generate the production stock cards of a sales order',
    'depends': ['web', 'pcs_document'],
    'data': [
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sis_report/static/src/js/sis_report.js',
            'sis_report/static/src/xml/sis_report.xml',
            'sis_report/static/src/css/sis_report.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
