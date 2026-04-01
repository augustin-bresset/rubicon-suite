{
    "name": "PDP",
    "version": "0.2.0",
    "license": "LGPL-3",
    "summary": "Frontend interface for Product Definition and Pricing",
    "depends": [
        "web",
        "pdp_price",
        "pdp_picture",
        "rubicon_uom",
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
        "web.assets_tests": [
            "pdp_frontend/static/tests/tours/tour_stone_manage.js",
            "pdp_frontend/static/tests/tours/tour_metal_parts.js",
            "pdp_frontend/static/tests/tours/tour_pdp_workspace.js",
        ],
    },
    "application": True,
    "installable": True,
}