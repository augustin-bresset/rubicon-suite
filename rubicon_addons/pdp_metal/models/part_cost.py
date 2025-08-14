from odoo import models, fields

class PartCost(models.Model):
    _name = 'pdp.part.cost'
    _description = 'Unit cost of a part'
    

    part    = fields.Many2one(
        comodel_name='pdp.part',
        required=True,
        ondelete='cascade',
    )
    purity  = fields.Many2one(
        comodel_name='pdp.metal.purity',
        required=True,
    )
    
    cost         = fields.Monetary(
        string='Unit Cost',
        currency_field="currency_id",
        required=True
    )

    currency_id  =  fields.Many2one(
        'res.currency',
        string='Currency'
    )
    