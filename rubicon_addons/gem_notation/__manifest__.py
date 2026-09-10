{
    'name': 'Gemstone Notation',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Technical',
    'summary': 'Standalone stone referential: pick components, get the code — and back',
    'description': """
A self-contained gemstone notation: the dictionaries of stone identities,
grades, hues and shapes with their codes, and the rule producing the
colour code of a finished product from its stones. Selecting a stone's
components gives its code and a code reads back into its components.

Token grammar PP[G][HH][SS]: stone (2 letters), grade (1 digit), hue
(digit + letter), shape (2 letters); blocks are omitted when they match
the stone's defaults — determined from occurrence counts in the actual
stone history — and every token parses without separators. See README.md
for the full documentation of the logic.

The module depends on 'base' only and carries no company data; wiring it
to an existing product database (transcription of real compositions,
verification of written codes, usage-based proposals) is the job of
separate bridge modules.
""",
    # 'web' only (shipped with every Odoo): the module must install on a
    # bare Odoo, on its own. A deployment-specific bridge may layer
    # stricter access rules on top.
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'data/gem.notation.category.csv',
        'data/gem.notation.grade.csv',
        'data/gem.notation.hue.csv',
        'data/gem.notation.shape.csv',
        'data/gem.notation.stone.csv',
        'views/notation_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'gem_notation/static/src/js/notation_workspace.js',
            'gem_notation/static/src/xml/notation_workspace.xml',
        ],
    },
    'installable': True,
    'application': False,
}
