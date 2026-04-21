from odoo import models, fields


class AlloyType(models.Model):
    _name = 'pdp.alloy.type'
    _description = 'Alloy Type'
    _rec_name = 'name'
    _order = 'code'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    main_metal_id = fields.Many2one(
        'pdp.raw.metal',
        string='Main Metal',
        help='Primary metal that defines this alloy type.',
    )
    purity_system = fields.Selection([
        ('carat', 'Carat'),
        ('millesimal', 'Millesimal'),
    ], string='Purity System')

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'Alloy type code must be unique.'),
    ]
