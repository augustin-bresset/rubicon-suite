{
    'name': 'PDP Labor',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['rubicon_env', 'pdp_product'],
    'data': [
        './security/ir.model.access.csv',
        # Views
        'views/pdp_views.xml',
        'views/pdp_menus.xml',

    ],
    'installable': True,
    'application': True,
}