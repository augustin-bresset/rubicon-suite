from odoo import models, fields

class Part(models.Model):
    """A `Part` is a part of a jewlery not made by Rubicon.

    """
    _name = 'pdp.part'
    _description = 'Piece (Part)'

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code must be unique !'),
    ]
    _rec_name = "code"

    code      = fields.Char(string='Code', required=True, size=5)
    name      = fields.Char(string='Name', required=True, size=50)
    costs  = fields.One2many(
        comodel_name='pdp.part.cost',
        inverse_name='part',
        string='Cost'
    )

