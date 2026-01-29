{
    'name': 'PDP Metal',
    'version': '0.02',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': ['rubicon_env'],           
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        # 'data/pdp.metal.purity.csv',
        # 'data/pdp.metal.csv',
        # 'data/pdp.part.csv',
        # 'data/pdp.part.cost.csv',
        
        # Views
        'views/pdp_views.xml',
        'views/pdp_menus.xml',
        ],                    
    'installable': True,
    'application': True,
}