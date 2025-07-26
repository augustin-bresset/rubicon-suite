{
    'name': 'PDP Product',
    'version': '0.01',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': ['base', 'pdp_metal', 'pdp_stone'],           
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        # 'data/pdp.product.category.csv',
        # 'data/pdp.product.model.csv',
        # 'data/pdp.product.model.matching.csv',
        # 'data/pdp.product.model.metal.csv',
        # 'data/pdp.product.csv',
        # 'data/pdp.product.stone.csv',
        # 'data/pdp.product.part.csv',
        
        # Views
        'views/pdp_views.xml',
        'views/pdp_menus.xml',
        ],                    
    'installable': True,
    'application': True,
}