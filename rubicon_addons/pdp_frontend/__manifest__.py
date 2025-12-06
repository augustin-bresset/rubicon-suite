{
    "name": "PDP Frontend",
    "version": "0.1.1",
    "license": "LGPL-3",
    "summary": "Frontend interface for Product Definition and Pricing",
    "depends": [
        "web",
        "pdp_price",
        "pdp_picture",
    ],
    "data": [
        "views/pdp_product_views.xml",
        "views/pdp_frontend_templates.xml",
        "views/pdp_menus.xml",
    ],
    "application": True,
    "installable": True,
}