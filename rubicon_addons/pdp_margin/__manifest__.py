{
    'name': 'PDP Margin',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'summary': "PDP Margin module to manage margin types and addons",
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
    'post_init_hook': 'post_init',
    'installable': True,
    'application': True,
}