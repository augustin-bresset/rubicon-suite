from odoo import models, fields

class Metal(models.Model):
    _name = 'pdp.metal'
    _table = 'metals'
    _description = 'Metal'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
    _rec_name='code'
    
    code         = fields.Char(string='Code', required=True, index=True)
    name         = fields.Char(string='Name', required=True)
    
    cost         = fields.Monetary(
        string='Unit Cost ($/once)',
        currency_field = "currency_id"
    )

    currency_id =  fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id
    )
    
    cost_method = fields.Selection(
        [('fixed', 'Fixed Cost'), ('market', 'Market Price')],
        string='Cost Method',
        default='fixed',
        required=True
    )
    market_metal_id = fields.Many2one(
        'pdp.market.metal',
        string='Market Metal'
    )
    
    plating      = fields.Boolean(string='Plating')
    gold         = fields.Boolean(string='Is Gold', default=True)
    reference    = fields.Boolean(string='Reference (18K gold)', default=False)
