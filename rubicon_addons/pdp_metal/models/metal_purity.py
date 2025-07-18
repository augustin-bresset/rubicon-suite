from odoo import models, fields

class MetalPurity(models.Model):
    """
    :note:: Metal Purity is an other way of saying Gold purity.
    """
    _name = 'pdp.metal.purity'
    _description = 'Metal Purity'
    # _sql_constraints = [
    #     ('name_unique', 'unique(name)', 'The name must be unique!'),
    # ]

    _rec_name = "code"
    
    code    = fields.Char(string='Name (e.g. 18K)', required=True, size=5)
    percent = fields.Float(
        string='Percentage',
        digits=(4, 1),
        help='e.g. 75.0 for 18K gold',
    )

