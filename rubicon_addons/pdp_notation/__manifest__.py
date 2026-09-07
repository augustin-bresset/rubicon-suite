{
    'name': 'PDP Notation',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Technical',
    'summary': 'Structured colour-code grammar: transcribe, look up, verify',
    'description': """
Grammar PP G BB EE for the colour segment of product codes:
PP = stone article (2 letters), G = grade (1 digit), BB = hue
(digit + letter), EE = shape (2 letters); blocks are omitted when they
match the article's defaults and the token parses without separators.
Dictionaries map the new codes to the legacy stone type / shade / shape
records, so codes can be transcribed both ways and an order's colour
code can be verified against its real stone composition.
""",
    'depends': ['pdp_stone', 'pdp_product', 'rubicon_env'],
    'data': [
        'security/ir.model.access.csv',
        'views/notation_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
