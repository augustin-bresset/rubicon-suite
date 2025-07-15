from odoo import models, fields

class Part(models.Model):
    """A `Part` is a part of a jewlery not made by Rubicon.

    """
    _name = 'rubicon.part'
    _table = 'parts'
    _description = 'Piece (Part)'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code must be unique !'),
        ('name_unique', 'unique(name)', 'Name must be unique !'),
    ]

    code      = fields.Char(string='Code', required=True, size=5)
    name      = fields.Char(string='Name', required=True, size=50)
    cost_ids  = fields.One2many(
        comodel_name='rubicon.part.cost',
        inverse_name='part_id',
        string='Cost',
        copy=True,
    )
