{
    "name": "PDP Picture",
    "version": "0.2.0",
    "summary": "Store large model pictures via filestore and show them on PDP models/products",
    "license": "LGPL-3",
    "category": "Product",
    "author": "Rubicon",
    "depends": ["pdp_product"],
    "data": [
        "security/ir.model.access.csv",
        "views/picture_views.xml",
        "views/pdp_menus.xml",
        # "views/inherit_model_views.xml",
        "views/test_picture_views.xml",
    ],
    "installable": True,
    "application": False,
} 