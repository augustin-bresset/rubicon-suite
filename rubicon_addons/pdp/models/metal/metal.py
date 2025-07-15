from odoo import models, fields

class Metal(models.Model):
    _name = 'rubicon.metal'
    _table = 'metals'
    _description = 'Metal'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    code         = fields.Char(string='Code', required=True, size=2)
    name         = fields.Char(string='Name', required=True, size=50)
    unit_cost    = fields.Float(
        string='Unit Cost (per kg)',
        digits=(18, 2),
        required=True,
    )
    currency_id  = fields.Many2one(
        comodel_name='rubicon.misc.currency',
        string='Currency',
        required=True,
    )
    plating      = fields.Boolean(string='Plating')
    is_gold      = fields.Boolean(string='Is Gold', default=True)
    purity_id    = fields.Many2one(
        comodel_name='rubicon.gold.purity',
        string='Gold Purity',
    )
    is_reference = fields.Boolean(string='Reference (18K gold)', default=False)
