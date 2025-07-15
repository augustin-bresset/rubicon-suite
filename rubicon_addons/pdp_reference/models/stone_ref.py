from odoo import models, fields

class StoneCategory(models.Model):
    _name = "pdp.stone.category"
    _description = "Stone Category"
    _table = "stone_categories"
    _auto  = False
    _rec_name = "name"

    id   = fields.Integer(string="ID", readonly=True)
    code = fields.Char(string="Code", readonly=False)
    name = fields.Char(string="Name", readonly=False)
    type_ids = fields.One2many(
        comodel_name="pdp.stone.type",
        inverse_name="category_id",
        string="Types",
    )

class StoneType(models.Model):
    _name = "pdp.stone.type"
    _description = "Stone Type"
    _table = "stone_types"
    _auto  = False
    _rec_name = "name"

    id          = fields.Integer(string="ID", readonly=True)
    code        = fields.Char(string="Code", readonly=False)
    name        = fields.Char(string="Name", readonly=False)
    density     = fields.Float(string="Density (g/cm³)", readonly=False)
    category_id = fields.Many2one(
        comodel_name="pdp.stone.category",
        string="Category",
        readonly=False,
    )

class StoneSize(models.Model):
    _name = "pdp.stone.size"
    _description = "Stone Size"
    _table = "stone_sizes"
    _auto  = False
    _rec_name = "size"

    size        = fields.Char(string="Size", readonly=False)
    description = fields.Char(string="Description", readonly=False)

class StoneShape(models.Model):
    _name = "pdp.stone.shape"
    _description = "Stone Shape"
    _table = "stone_shapes"
    _auto  = False
    _rec_name = "shape"

    id    = fields.Integer(string="ID", readonly=True)
    code  = fields.Char(string="Code", readonly=False)
    shape = fields.Char(string="Shape", readonly=False)

class StoneShade(models.Model):
    _name = "pdp.stone.shade"
    _description = "Stone Shade"
    _table = "stone_shades"
    _auto  = False
    _rec_name = "shade"

    id    = fields.Integer(string="ID", readonly=True)
    code  = fields.Char(string="Code", readonly=False)
    shade = fields.Char(string="Shade", readonly=False)