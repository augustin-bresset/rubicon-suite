{
    'name': 'PDP Stone',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': ['rubicon_env'],           
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/pdp.stone.category.csv',
        'data/pdp.stone.type.csv',
        'data/pdp.stone.shape.csv',
        'data/pdp.stone.size.csv',
        'data/pdp.stone.shade.csv',
        'data/pdp.stone.weight.csv',
        'data/pdp.stone.csv',
        # Views
        'views/pdp_views.xml',
        'views/pdp_menus.xml',
        ],                    
    'installable': True,
    'application': True,
}