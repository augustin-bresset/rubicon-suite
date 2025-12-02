{
    "name": "PDP Frontend",
    "version": "0.1.0",
    "license": "LGPL-3",
    "summary": "Frontend interface for Product Definition and Pricing",
    "depends": [
        "pdp_product",
        "pdp_price",
        "pdp_margin",
        "pdp_metal",
        "pdp_picture",
    ],
    "data": [
        "views/pdp_product_views.xml",
        "views/pdp_menus.xml",
    ],
    "application": True,
    "installable": True,
}