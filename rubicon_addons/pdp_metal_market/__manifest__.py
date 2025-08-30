{
    "name": "PDP Metal Market",
    "version": "18.0.1.0.0",
    "depends": ["base", "pdp_metal"],
    "data": [
        "security/ir.model.access.csv",
        "data/market_metal.xml",        # AU, AG, PD, CU, SN, ...
        "data/cron.xml",                # désactivé par défaut si provider non config
        "views/market_views.xml",
    ],
    "installable": True,
}
