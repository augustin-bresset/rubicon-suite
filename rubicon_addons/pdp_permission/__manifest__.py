{
    "name": "PDP Permissions",
    "version": "1.0.0",
    "summary": "Dynamic Role-Based Access Control for PDP",
    "category": "Technical",
    "license": "LGPL-3",
    "depends": [
        "base",
        "pdp_api",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/pdp_permission_data.xml",
        "views/pdp_permission_views.xml",
        "views/pdp_permission_menus.xml",
    ],
    "installable": True,
    "application": False,
}
