from odoo import models, fields

class PartCost(models.Model):
    _name = 'pdp.part.cost'
    _description = 'Unit cost of a part'
    

    part_code    = fields.Many2one(
        comodel_name='pdp.part',
        required=True,
        ondelete='cascade',
    )
    purity_code  = fields.Many2one(
        comodel_name='pdp.metal.purity',
        required=True,
    )
    cost         = fields.Float(
        string='Unit Cost (USD)',
        digits=(10, 2),
        required=True,
    )

