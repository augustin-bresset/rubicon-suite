{
    'name': 'PDP Margin',
    'version': '0.01',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': ['base'],           
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