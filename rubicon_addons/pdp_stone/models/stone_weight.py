from odoo import models, fields, api

class StoneWeight(models.Model):
    """Weight for a specific type, shape, shade and size of stone.
    It is used mainly because you don't have to specify the shape or shade for having result.
    """
    _name = "pdp.stone.weight"
    _description = "Stone Weight"


    weight = fields.Float(
        string='Weight (carat)',
        digits=(7, 4),
        required=True
    )

    type_id  = fields.Many2one("pdp.stone.type",  string="Stone Type",  required=True, index=True, ondelete="cascade")
    shape_id = fields.Many2one("pdp.stone.shape", string="Stone Shape", required=True, index=True, ondelete="cascade")
    shade_id = fields.Many2one("pdp.stone.shade", string="Stone Shade", required=False, default=None, index=True, ondelete="set null")
    size_id  = fields.Many2one("pdp.stone.size",  string="Stone Size",  required=True, index=True, ondelete="cascade")


    _sql_constraints = [
        (
            "stone_weight_uniq",
            "unique(type_id, shape_id, size_id, shade_id)",
            "A weight already exists for this type/shape/size/shade combination."
        ),
        (
            "weight_positive",
            "CHECK(weight > 0)",
            "Weight must be positive."
        ),
    ]

    _order = "type_id, shape_id, shade_id, size_id"

    def name_get(self):
        res = []
        for rec in self:
            parts = [
                rec.type_id.code or rec.type_id.name,
                rec.shape_id.name if rec.shape_id else "-",
                rec.shade_id.name if rec.shade_id else "-",
                rec.size_id.name if rec.size_id else "-",
            ]
            label = f"{'/'.join(parts)} → {rec.weight} ct"
            res.append((rec.id, label))
        return res

    # ------------------------------------------------------------------
    # Propagation to pdp.stone.weight_id
    #
    # pdp.stone._compute_weight_id() searches this catalogue but cannot
    # @api.depends on it, so a stored weight_id stays stale when a weight row
    # is created/changed/removed. Push the refresh back to the matching stones.
    # ------------------------------------------------------------------

    def _matching_stones(self):
        """Stones whose (type, shape, size) match any of these weight rows."""
        Stone = self.env['pdp.stone']
        stones = Stone.browse()
        for rec in self:
            if rec.type_id and rec.shape_id and rec.size_id:
                stones |= Stone.search([
                    ('type_id', '=', rec.type_id.id),
                    ('shape_id', '=', rec.shape_id.id),
                    ('size_id', '=', rec.size_id.id),
                ])
        return stones

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._matching_stones()._recompute_weight_id()
        return records

    def write(self, vals):
        before = self._matching_stones()
        res = super().write(vals)
        (before | self._matching_stones())._recompute_weight_id()
        return res

    def unlink(self):
        stones = self._matching_stones()
        res = super().unlink()
        stones._recompute_weight_id()
        return res