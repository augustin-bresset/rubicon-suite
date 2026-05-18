{
    'name': 'Analysis',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Sales',
    'summary': 'Sales & Orders pivot analysis',
    'depends': ['base', 'sis_document', 'sis_party'],
    'data': [
        'views/analysis_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sis_analysis/static/src/scss/pivot_sticky.scss',
        ],
    },
    'installable': True,
    'application': False,
}
