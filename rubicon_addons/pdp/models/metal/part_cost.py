from odoo import models, fields

class PartCost(models.Model):
    _name = 'rubicon.part.cost'
    _table = 'part_costs'
    _description = 'Unit cost of a part'

    part_id      = fields.Many2one(
        comodel_name='rubicon.part',
        string='Piece',
        required=True,
        ondelete='cascade',
    )
    purity_id    = fields.Many2one(
        comodel_name='rubicon.gold.purity',
        string='Purity',
        required=True,
    )
    cost         = fields.Float(
        string='Unit Cost',
        digits=(10, 2),
        required=True,
    )
    currency_id  = fields.Many2one(
        comodel_name='rubicon.misc.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env['rubicon.misc.currency'].search([('code', '=', 'USD')], limit=1).id,
    )
    

