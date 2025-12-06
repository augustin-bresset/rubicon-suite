{
    'name': 'PDP Price',
    'version': '0.01',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': [
        'rubicon_env', 'pdp_labor', 'pdp_margin'
        ],    
           
    'data': [
        # Security
        'security/ir.model.access.csv',
    
        # Views
        'views/price_preview_views.xml',
        'views/pdp_menus.xml',
        ],   
    'installable': True,
    'application': True,
}