from odoo import models, fields, api


class Alloy(models.Model):
    _name = 'pdp.alloy'
    _description = 'Metal Alloy'
    _rec_name = 'name'
    _order = 'code'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    purity = fields.Char(
        string='Purity',
        help='Purity of the main metal, e.g. 18k, 925, 750.',
    )
    main_metal_id = fields.Many2one(
        'pdp.raw.metal',
        string='Main Metal',
        help='The primary metal in this alloy.',
    )
    component_ids = fields.One2many(
        'pdp.alloy.component',
        'alloy_id',
        string='Composition',
    )
    total_ratio = fields.Float(
        string='Total Ratio',
        compute='_compute_total_ratio',
        digits=(10, 4),
        store=False,
    )

    @api.depends('component_ids.ratio')
    def _compute_total_ratio(self):
        for alloy in self:
            alloy.total_ratio = sum(alloy.component_ids.mapped('ratio'))

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'Alloy code must be unique.'),
    ]


class AlloyComponent(models.Model):
    _name = 'pdp.alloy.component'
    _description = 'Alloy Component'
    _order = 'ratio desc'

    alloy_id = fields.Many2one(
        'pdp.alloy',
        string='Alloy',
        required=True,
        ondelete='cascade',
        index=True,
    )
    metal_id = fields.Many2one(
        'pdp.raw.metal',
        string='Metal',
        required=True,
    )
    ratio = fields.Float(
        string='Ratio',
        digits=(10, 4),
        default=0.0,
        help='Proportion of this metal in the alloy (0.0 to 1.0). Example: 0.75 for 75%.',
    )
