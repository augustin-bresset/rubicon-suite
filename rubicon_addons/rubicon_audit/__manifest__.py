{
    'name': 'Rubicon Change History',
    'summary': 'Who changed which price, when, and why — without the mail stack',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'depends': [
        'pdp_base', 'pdp_stone', 'pdp_metal', 'pdp_labor', 'pdp_margin',
        'sis_document',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/audit_log_views.xml',
    ],
    'installable': True,
}
