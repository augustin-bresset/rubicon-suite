{
    "name": "PDP",
    "version": "0.2.0",
    "license": "LGPL-3",
    "summary": "Frontend interface for Product Definition and Pricing",
    "depends": [
        "web",
        "pdp_api",
        "pdp_picture",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/pdp_currency_setting_views.xml",
        "views/pdp_product_views.xml",
        "views/pdp_frontend_templates.xml",
        "views/pdp_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pdp_frontend/static/src/**/*",
        ],
    },
    "application": True,
    "installable": True,
}