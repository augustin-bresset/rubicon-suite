import base64
import hashlib

from odoo import api, fields, models


class Picture(models.Model):
    _name = "pdp.picture"
    _description = "Picture linked to a PDP model"
    _order = "id desc"
    _sql_constraints = [
        ("picture_unique_model", "unique(model_id)", "A model can only have one picture."),
    ]

    model_id = fields.Many2one(
        "pdp.product.model",
        string="Model",
        ondelete="set null",
        index=True,
    )

    image_1920 = fields.Image(
        string="Image",
        max_width=1920,
        max_height=1920,
        required=True,
        attachment=True,
    )
    image = fields.Image(related="image_1920", readonly=False)

    filename = fields.Char(string="Filename")

    checksum = fields.Char(string="Checksum", index=True, readonly=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            payload = vals.get("image") or vals.get("image_1920")
            if payload and not vals.get("checksum"):
                vals["checksum"] = hashlib.md5(base64.b64decode(payload)).hexdigest()
        return super().create(vals_list)

    def write(self, vals):
        payload = vals.get("image") or vals.get("image_1920")
        if payload:
            vals["checksum"] = hashlib.md5(base64.b64decode(payload)).hexdigest()
        return super().write(vals)