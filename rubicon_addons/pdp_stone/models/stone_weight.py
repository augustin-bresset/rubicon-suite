from odoo import models, fields

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

    type_id  = fields.Many2one("pdp.stone.type",  string="Stone Type",  required=True, index=True)
    shape_id = fields.Many2one("pdp.stone.shape", string="Stone Shape", required=True, index=True)
    shade_id = fields.Many2one("pdp.stone.shade", string="Stone Shade", index=True)
    size_id  = fields.Many2one("pdp.stone.size",  string="Stone Size",  required=True, index=True)


    _sql_constraints = [
        (
            "stone_weight_uniq",
            "unique(type_id, shape_id, size_id)",
            "A weight already exists for this type/shape/size combination."
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