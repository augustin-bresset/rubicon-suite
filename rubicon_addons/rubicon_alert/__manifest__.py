{
    'name': 'Rubicon Alerts',
    'summary': 'Operational alerts computed live: overdue orders, stuck WIP, unscanned barcodes, stale rates',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'depends': ['rubicon_env', 'pdp_base', 'sis_document', 'pcs_document', 'rubicon_audit'],
    'data': [
        'security/ir.model.access.csv',
        'views/alert_views.xml',
    ],
    'installable': True,
}
