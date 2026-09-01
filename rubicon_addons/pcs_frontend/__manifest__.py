{
    'name': 'PCS',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Manufacturing',
    'summary': 'PCS — Production Control System workspace: documents, barcode scanning, dashboard and reports',
    'depends': ['web', 'pcs_document'],
    'data': [
        'security/ir.model.access.csv',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pcs_frontend/static/src/js/pcs_workspace.js',
            'pcs_frontend/static/src/xml/pcs_workspace.xml',
            'pcs_frontend/static/src/css/pcs_workspace.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
