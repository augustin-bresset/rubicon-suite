{
    'name': 'PDP',
    'version': '0.01',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': ['base'],           
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/pdp.stone.category.csv',
        'data/pdp.stone.type.csv',
        'data/pdp.stone.shape.csv',
        'data/pdp.stone.size.csv',
        'data/pdp.stone.shade.csv',
        
        # Views
        'views/pdp_actions_menu.xml',
        'views/stone_shade_views.xml',
        'views/stone_shape_views.xml',
        'views/stone_size_views.xml'
        # 'views/stone_type_views.xml'
        ],                    
    'installable': True,
    'application': True,
}