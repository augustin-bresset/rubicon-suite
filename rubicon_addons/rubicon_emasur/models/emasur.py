from odoo import fields, models


class EmasurStone(models.Model):
    """One Emasur "pierre validée": a species + colour in a single flat code.

    Equivalent, on the Rubicon side, to a (stone type, shade) pair. The rows
    come from Emasur's validated list (data/emasur.stone.csv); the Rubicon
    columns were pre-matched by name and are meant to be curated here.
    An entry with no shade is the generic species entry: it is what a bare
    Rubicon type code converts to.
    """
    _name = 'emasur.stone'
    _description = 'Emasur validated stone'
    _rec_name = 'code'
    _order = 'code'

    code = fields.Char(required=True, index=True)
    name = fields.Char(string='Name (EN)', required=True)
    french_name = fields.Char(string='Name (FR)')
    type_id = fields.Many2one('pdp.stone.type', string='Rubicon Type', index=True)
    shade_id = fields.Many2one('pdp.stone.shade', string='Rubicon Shade')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Each Emasur stone code must be unique.'),
    ]


class EmasurShape(models.Model):
    _name = 'emasur.shape'
    _description = 'Emasur stone shape (forme)'
    _rec_name = 'code'
    _order = 'code'

    code = fields.Char(required=True, index=True)
    name = fields.Char(string='Name (EN)', required=True)
    french_name = fields.Char(string='Name (FR)')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Each Emasur shape code must be unique.'),
    ]


class EmasurCut(models.Model):
    _name = 'emasur.cut'
    _description = 'Emasur lapidary cut (taille de lapidaire)'
    _rec_name = 'code'
    _order = 'code'

    code = fields.Char(required=True, index=True)
    name = fields.Char(string='Name (EN)', required=True)
    french_name = fields.Char(string='Name (FR)')
    description = fields.Char()

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Each Emasur cut code must be unique.'),
    ]


class EmasurShapeMap(models.Model):
    """Rubicon merges the geometry and the lapidary cut in one shape record
    ("Oval Cabochon"); Emasur keeps them apart. One row per Rubicon shape."""
    _name = 'emasur.shape.map'
    _description = 'Rubicon shape to Emasur shape and cut'
    _rec_name = 'rubicon_shape_id'
    _order = 'rubicon_shape_id'

    rubicon_shape_id = fields.Many2one(
        'pdp.stone.shape', required=True, index=True, ondelete='cascade')
    shape_id = fields.Many2one('emasur.shape', string='Emasur Shape')
    cut_id = fields.Many2one('emasur.cut', string='Emasur Cut')

    _sql_constraints = [
        ('rubicon_shape_unique', 'UNIQUE(rubicon_shape_id)',
         'A Rubicon shape maps to at most one Emasur shape/cut pair.'),
    ]


class EmasurTokenAlias(models.Model):
    """Legacy Rubicon colour tokens that are not stone type codes.

    Old design codes abbreviate freely (TT, DT, L.AM, PL...). Each alias
    states which (type, shade) the token means, so the converter can read
    historical codes; the list is meant to grow by curation.
    """
    _name = 'emasur.token.alias'
    _description = 'Legacy colour-token alias'
    _rec_name = 'token'
    _order = 'token'

    token = fields.Char(required=True, index=True)
    type_id = fields.Many2one('pdp.stone.type', string='Rubicon Type', required=True)
    shade_id = fields.Many2one('pdp.stone.shade', string='Rubicon Shade')

    _sql_constraints = [
        ('token_unique', 'UNIQUE(token)', 'Each legacy token can only have one alias.'),
    ]
