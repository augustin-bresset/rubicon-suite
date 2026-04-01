{
    'name': 'PDP Margin',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': ['rubicon_env', 'pdp_stone', 'pdp_metal', 'pdp_labor', 'pdp_labor'],           
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        # 'data/pdp.margin.csv',
        
        
        # Views
        'views/pdp_views.xml',
        'views/pdp_menus.xml',
        ],                    
    'installable': True,
    'application': True,
}