{
    'name': 'PCS Simulator',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Manufacturing',
    'summary': 'Factory simulator for PCS — replays the production process through the real scan API',
    'depends': ['pcs_frontend'],
    'data': [
        'security/ir.model.access.csv',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pcs_simulator/static/src/js/pcs_simulator.js',
            'pcs_simulator/static/src/xml/pcs_simulator.xml',
            'pcs_simulator/static/src/css/pcs_simulator.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
