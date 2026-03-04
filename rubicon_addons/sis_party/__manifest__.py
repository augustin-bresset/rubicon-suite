{
    'name': 'SIS Party',
    'version': '18.0.2.0.0',
    'category': 'Sales',
    'summary': 'SIS Party (Client/Vendor) Management — extends res.partner',
    'depends': ['base', 'pdp_margin'],
    'data': [
        'security/ir.model.access.csv',
        'data/sis.pay.term.csv',
        'data/sis.shipper.csv',
        'data/sis.trade.fair.csv',
        'views/partner_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
