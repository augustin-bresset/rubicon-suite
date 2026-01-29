from odoo import models, fields

class ModelMetal(models.Model):
    _name = 'pdp.product.model.metal'
    _description = 'Model Metal with quantity'

    
    weight = fields.Float(
        string='Weight in reference Metal (g)',
        digits=(6, 3),
        required=True
    )
    
    metal_version = fields.Char(
        string="Version of Metal (W, W2, ...)",
        required=True
        )
    
    metal_id  = fields.Many2one(
        comodel_name='pdp.metal',
        string='Metal Code',
        index=True
    )
    
    purity_id  = fields.Many2one(
        comodel_name='pdp.metal.purity',
        string='Metal Purity',
        index=True
    )

    model_id = fields.Many2one(
        'pdp.product.model', 
        required=True, 
        index=True,
        )

    # =========================================================================
    # Domain Methods - Reusable by API, Cron, OWL, Reports
    # =========================================================================

    def to_dict(self):
        """Return metal weight data as JSON-serializable dict."""
        return {
            'metal': self.metal_id.name if self.metal_id else '',
            'metal_code': self.metal_id.code if self.metal_id else '',
            'purity': self.purity_id.code if self.purity_id else '',
            'weight': self.weight,
            'version': self.metal_version,
        }