{
    'name': 'Rubicon Notation',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Technical',
    'summary': 'Standalone stone referential: pick components, get the code — and back',
    'description': """
An independent stone referential — its own catalogue of stone identities,
grades, hues and shapes — where selecting a stone's components gives its
code and a code reads back into its components. Not a translation layer:
the Rubicon-Emasur conversion is rubicon_emasur's job, and this module
depends on no company data, so either company runs it as-is. Token
grammar PP[G][BB][EE]: article (2 letters), grade (1 digit), hue
(digit + letter), shape (2 letters); blocks are omitted on the article's
defaults and every token parses without separators. The optional wiring
to the PDP stone data (transcription of real compositions, order
verification, proposals from usage) lives in rubicon_notation_pdp.
""",
    # 'base' only: the module must install on a bare Odoo, outside this
    # suite. The suite's 3-level access policy is layered on by the bridge.
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/notation_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
