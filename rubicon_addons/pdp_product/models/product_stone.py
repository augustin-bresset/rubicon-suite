from odoo import models, fields, api

class ProductStone(models.Model):
    _name = 'pdp.product.stone'
    _description = 'Product Stone'

    stone_id = fields.Many2one(
        comodel_name='pdp.stone',
        string='Stone Code Buyed',
        required=True,
        index=True
    )
    
    pieces = fields.Integer(
        string="Number of stones",
        required=True,
        default=1
    )
    
    weight = fields.Float(
        string="Weight of one stone buyed",
        compute="_compute_weight",
        store=True,
        readonly=False,
        digits=(7, 4),
    )

    reshaped_shape_id = fields.Many2one(
        comodel_name='pdp.stone.shape',
        string='Shape of Stone Reshaped',
    )
    
    reshaped_size_id  = fields.Many2one(
        comodel_name='pdp.stone.size',
        string='Size of Stone Code Reshaped for product',
    )
    
    reshaped_weight = fields.Char(
        string="Weight of one stone used",   
    )
    
    composition_id = fields.Many2one(
        comodel_name='pdp.product.stone.composition',
        string='Composition',
        required=True,
        ondelete='cascade'
    )

    @api.depends('stone_id', 'stone_id.weight')
    def _compute_weight(self):
        for record in self:
            if not record.weight or record.weight == 0.0:
                record.weight = record.stone_id.weight

    # =========================================================================
    # Domain Methods - Reusable by API, Cron, OWL, Reports
    # =========================================================================

    def to_dict_original(self):
        """Return original stone data (as purchased)."""
        return {
            'type': self.stone_id.type_id.name if self.stone_id.type_id else '',
            'shade': self.stone_id.shade_id.shade if self.stone_id.shade_id else '',
            'shape': self.stone_id.shape_id.shape if self.stone_id.shape_id else '',
            'pieces': self.pieces,
            'weight': self.weight,
        }

    def to_dict_recut(self):
        """Return recut stone data (after reshaping)."""
        recut_shape = self.reshaped_shape_id.shape if self.reshaped_shape_id else (
            self.stone_id.shape_id.shape if self.stone_id.shape_id else ''
        )
        return {
            'type': self.stone_id.type_id.name if self.stone_id.type_id else '',
            'shade': self.stone_id.shade_id.shade if self.stone_id.shade_id else '',
            'shape': recut_shape,
            'pieces': self.pieces,
            'weight': self.reshaped_weight or self.weight,
        }

    def to_dict(self):
        """Return complete stone line data."""
        return {
            'stone_code': self.stone_id.code if self.stone_id else '',
            'type': self.stone_id.type_id.name if self.stone_id.type_id else '',
            'shade': self.stone_id.shade_id.shade if self.stone_id.shade_id else '',
            'shape': self.stone_id.shape_id.shape if self.stone_id.shape_id else '',
            'pieces': self.pieces,
            'weight': self.weight,
            'reshaped_shape': self.reshaped_shape_id.shape if self.reshaped_shape_id else '',
            'reshaped_weight': self.reshaped_weight,
        }