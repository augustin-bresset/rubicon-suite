{
    'name': 'Gemstone Notation - PDP Bridge',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Technical',
    'summary': 'Wire the notation dictionaries to the PDP stone data',
    'description': """
Rubicon-side integration of the shared notation core: links the notation
articles/shapes to the legacy pdp.stone dictionaries, maps legacy shades
to grade/hue pairs, transcribes a product's real stone composition into
the new colour code, verifies a written colour code against it, and
proposes dictionary codes from actual usage. Emasur runs the core module
alone; everything PDP-specific lives here.
""",
    'depends': ['gem_notation', 'pdp_stone', 'pdp_product'],
    'data': [
        'security/ir.model.access.csv',
        'views/bridge_views.xml',
    ],
    'installable': True,
    'application': False,
}
