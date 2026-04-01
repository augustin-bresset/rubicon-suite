{
    'name': 'SIS Frontend',
    'version': '1.1',
    'license': 'LGPL-3',
    'category': 'Sales',
    'summary': 'Frontend application for Sales Information System (SIS)',
    'description': """
        Provides a dedicated frontend UI for SIS, mimicking the original layout
        but integrated cleanly into Odoo's environment.
    """,
    'author': 'Rubicon',
    'depends': ['base', 'web', 'sis_party', 'sis_document'],
    'data': [
        'views/sis_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sis_frontend/static/src/js/sis_dashboard.js',
            'sis_frontend/static/src/xml/sis_dashboard.xml',
            'sis_frontend/static/src/js/sis_workspace.js',
            'sis_frontend/static/src/xml/sis_workspace.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
