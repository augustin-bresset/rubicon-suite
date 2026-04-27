from odoo import fields, models


class MarginStone(models.Model):
    _name = "pdp.margin.stone"
    _description = "Stone Margin"

    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True,
        ondelete="cascade",
    )
    stone_type_id = fields.Many2one(
        string="Stone Type",
        comodel_name="pdp.stone.type",
        index=True,
    )
    stone_shape_id = fields.Many2one(
        string="Shape",
        comodel_name="pdp.stone.shape",
        index=True,
    )
    stone_size_id = fields.Many2one(
        string="Size",
        comodel_name="pdp.stone.size",
        index=True,
    )
    stone_shade_id = fields.Many2one(
        string="Shade",
        comodel_name="pdp.stone.shade",
        index=True,
    )
    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
