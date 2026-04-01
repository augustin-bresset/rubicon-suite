{
    'name': 'SIS Document',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Sales',
    'summary': 'SIS Sales Documents (Quotations, Orders, Invoices)',
    'depends': ['base', 'sis_party', 'pdp_product'],
    'data': [
        'security/ir.model.access.csv',
        'data/sis.doc.type.csv',
        'data/sis.doc.in.mode.csv',
        # sis.document and sis.document.item are business data — loaded via import_sis_odoo.py
        'report/report_action.xml',
        'report/report_sis_document.xml',
        'views/document_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'sis_document/static/src/scss/variables.scss'),
        ],
        'web.assets_backend': [
            'sis_document/static/src/scss/style.scss',
        ],
    },
    'installable': True,
    'application': False,
}
