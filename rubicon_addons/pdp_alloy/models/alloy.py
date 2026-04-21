from odoo import models, fields, api


class Alloy(models.Model):
    _name = 'pdp.alloy'
    _description = 'Metal Alloy'
    _rec_name = 'name'
    _order = 'code'

    type_id = fields.Many2one(
        'pdp.alloy.type',
        string='Type',
        help='e.g. Yellow Gold, White Gold, Silver …',
    )
    purity_id = fields.Many2one(
        'pdp.alloy.purity',
        string='Purity',
    )
    variant = fields.Char(
        string='Variant',
        default='',
        help='Optional suffix for alloys sharing the same type and purity (e.g. HARD, SOFT, V2).',
    )
    code = fields.Char(
        string='Code',
        compute='_compute_code',
        store=True,
        readonly=True,
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        readonly=True,
    )
    component_ids = fields.One2many(
        'pdp.alloy.component',
        'alloy_id',
        string='Composition',
    )
    density = fields.Float(
        string='Density (g/cm³)',
        compute='_compute_density',
        store=True,
        digits=(10, 4),
        help='Weighted average density computed from the composition ratios.',
    )
    total_ratio = fields.Float(
        string='Total Ratio',
        compute='_compute_total_ratio',
        digits=(10, 4),
        store=False,
    )

    @api.depends('type_id', 'purity_id', 'variant')
    def _compute_code(self):
        for alloy in self:
            base = (alloy.type_id.code or '') + (alloy.purity_id.code or '')
            alloy.code = (base + '-' + alloy.variant) if alloy.variant else base

    @api.depends('type_id', 'purity_id')
    def _compute_name(self):
        for alloy in self:
            parts = []
            if alloy.type_id:
                parts.append(alloy.type_id.name)
            if alloy.purity_id:
                parts.append(alloy.purity_id.code)
            alloy.name = ' '.join(parts) if parts else (alloy.code or '')

    @api.depends('component_ids.ratio', 'component_ids.metal_id', 'component_ids.metal_id.density')
    def _compute_density(self):
        for alloy in self:
            alloy.density = sum(
                c.ratio * (c.metal_id.density or 0.0)
                for c in alloy.component_ids
            )

    @api.depends('component_ids.ratio')
    def _compute_total_ratio(self):
        for alloy in self:
            alloy.total_ratio = sum(alloy.component_ids.mapped('ratio'))

    def convert_weight(self, weight, to_alloy):
        """Return the weight of the same volume cast in `to_alloy`.

        Formula: w_new = w_ref × (density_new / density_ref)

        Returns False if self has no density (composition incomplete).
        """
        self.ensure_one()
        if not self.density:
            return False
        if not to_alloy.density:
            return False
        return weight * to_alloy.density / self.density

    _sql_constraints = [
        ('type_purity_variant_uniq', 'UNIQUE(type_id, purity_id, variant)', 'This type + purity + variant combination already exists.'),
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
