{
    "name": "PDP Frontend",
    "version": "0.1.1",
    "license": "LGPL-3",
    "summary": "Frontend interface for Product Definition and Pricing",
    "depends": [
        "web",
        "pdp_picture",
        "pdp_price",
        "pdp_product",
        "pdp_labor",
        "pdp_metal",
        "pdp_stone",
        "pdp_margin",
    ],
    "data": [
        "views/pdp_product_views.xml",
        "views/pdp_frontend_templates.xml",
        "views/pdp_menus.xml",
    ],
    "application": True,
    "installable": True,
}