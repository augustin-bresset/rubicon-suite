{
    'name': 'SIS Document',
    'version': '18.0.1.3.0',
    'license': 'LGPL-3',
    'category': 'Sales',
    'summary': 'SIS Sales Documents (Quotations, Orders, Invoices)',
    'depends': ['base', 'sis_party', 'pdp_product', 'rubicon_frontend'],
    'data': [
        'security/ir.model.access.csv',
        'data/sis.doc.type.csv',
        'data/doc_type_remarks.xml',
        'data/sis.doc.in.mode.csv',
        # sis.document and sis.document.item are business data — loaded via ops/migration/import/import_sis_documents.py
        'report/report_action.xml',
        'report/report_sis_document.xml',
        'wizard/print_wizard_views.xml',
        'views/document_views.xml',
        'views/doc_type_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
