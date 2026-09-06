{
    'name': 'Rubicon / Emasur Notation',
    'summary': 'Convert stone and design codes between the Rubicon and Emasur notation systems',
    'version': '18.0.1.2',
    'license': 'LGPL-3',
    'depends': ['pdp_product', 'sis_document'],
    'data': [
        'security/ir.model.access.csv',
        'data/emasur.shape.csv',
        'data/emasur.cut.csv',
        'data/emasur.stone.csv',
        'data/emasur.token.alias.csv',
        'data/emasur.shape.map.csv',
        'views/emasur_views.xml',
    ],
    'installable': True,
}
