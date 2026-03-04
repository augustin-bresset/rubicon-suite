from odoo import models, fields

class ProductStoneComposition(models.Model):
    _name = 'pdp.product.stone.composition'
    _description = 'Group of stones used in a product (without metal)'
    _rec_name = 'code'

    code = fields.Char(string='Composition Code', required=True, index=True)
    
    stone_line_ids = fields.One2many(
        comodel_name='pdp.product.stone',
        inverse_name='composition_id',
        string='Stone Lines'
    )

    # =========================================================================
    # Domain Methods - Reusable by API, Cron, OWL, Reports
    # =========================================================================

    def to_dict_list(self):
        """Return all stone lines as list of dicts."""
        self.ensure_one()
        return [line.to_dict() for line in self.stone_line_ids]

    def get_weight_summary(self):
        """Compute total weight and pieces for this composition."""
        self.ensure_one()
        total_weight = 0.0
        total_pieces = 0
        for line in self.stone_line_ids:
            total_pieces += line.pieces
            w = line.weight or 0.0
            total_weight += w * line.pieces
        return {
            'total_weight': total_weight,
            'total_pieces': total_pieces,
        }
