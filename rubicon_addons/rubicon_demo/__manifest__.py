{
    'name': 'Rubicon Demo Data',
    'version': '0.1.0',
    'license': 'LGPL-3',
    'depends': [
        'pdp_frontend',
        'sis_frontend',
        'rubicon_uom',
    ],
    'data': ['data/rubicon_demo_data.xml'],
    'pre_init_hook': 'pre_init_hook',
    'installable': True,
    'application': False,
}
