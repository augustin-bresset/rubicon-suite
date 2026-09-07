{
    'name': 'Rubicon Notation',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Technical',
    'summary': 'Structured colour-code grammar: dictionaries, parse, build, look up',
    'description': """
Company-neutral core of the structured colour codation, shared by Rubicon
and Emasur. Token grammar PP[G][BB][EE]: article (2 letters), grade
(1 digit), hue (digit + letter), shape (2 letters); blocks are omitted on
the article's defaults and every token parses without separators. The
dictionaries stand alone — no PDP dependency — so the module is usable by
itself; the PDP integration (transcription of real compositions, order
verification, proposals from usage) lives in rubicon_notation_pdp.
""",
    'depends': ['rubicon_env'],
    'data': [
        'security/ir.model.access.csv',
        'views/notation_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
