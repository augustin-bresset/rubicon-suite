{
    'name': 'PDP Picture',
    'version': '0.1.0',
    'summary': "Store large model pictures via filestore and show them on PDP models/products",
    'license': 'LGPL-3',
    'category': 'Product',
    'author': 'Rubicon',
    'depends': ['pdp_product'],  # we extend pdp.product.model & pdp.product forms
    'data': [
        'security/ir.model.access.csv',
        'views/picture_views.xml',
        'views/inherit_model_views.xml',
    ],
    'installable': True,
    'application': False,
}