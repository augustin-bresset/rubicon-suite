from odoo import models, fields

class Metal(models.Model):
    _name = 'pdp.metal'
    _table = 'metals'
    _description = 'Metal'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
    _rec_name='code'
    
    code         = fields.Char(string='Code', required=True, size=2)
    name         = fields.Char(string='Name', required=True, size=20)
    
    cost         = fields.Monetary(
        string='Unit Cost ($/kg)',
        currency_field = "currency_id"
    )

    currency_id =  fields.Many2one(
        'res.currency',
        string='Currency',
        default='USD'
    )
    
    plating      = fields.Boolean(string='Plating')
    gold         = fields.Boolean(string='Is Gold', default=True)
    reference    = fields.Boolean(string='Reference (18K gold)', default=False)
