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
    
    plating          = fields.Boolean(string='Plating')
    gold             = fields.Boolean(string='Is Gold', default=True)
    is_reference     = fields.Boolean(
        string='Reference Metal',
        default=False,
        help='Mark as the reference metal for Metal Conv computation (should be White Gold 18K).',
    )
    density          = fields.Float(
        string='Density (g/cm³)',
        digits=(16, 4),
        help='Alloy density at typical purity (e.g. WG18K ≈ 15.5, Silver 925 ≈ 10.3).',
    )
    default_purity_id = fields.Many2one(
        'pdp.metal.purity',
        string='Default Purity',
    )
    purity_system = fields.Selection(
        [('carat', 'Carat'), ('millesimal', 'Millièmes')],
        string='Purity System',
    )
