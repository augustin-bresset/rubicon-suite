{
    'name': 'Rubicon Frontend',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Technical',
    'summary': 'Shared SCSS design tokens and theme for Rubicon suite',
    'depends': ['web'],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'rubicon_frontend/static/src/scss/variables.scss'),
        ],
        'web.assets_backend': [
            'rubicon_frontend/static/src/scss/odoo_overrides.scss',
            'rubicon_frontend/static/src/scss/workspace.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
