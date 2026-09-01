{
    'name': 'PDF Generator',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Augustin Bresset',
    'depends': ['base', 'rubicon_env'],
    'data': [
        'security/ir.model.access.csv',
        # Views
        # 'views/pdfg_views.xml',
        'views/pdfg_menus.xml',
        'views/pdfg_template_views.xml',
        
        ],                    
    'installable': True,
    'application': True,
}