from odoo import models, fields


class StoneType(models.Model):
    """
    :note::
     The density was written in reference of the quartz. (2.65gm/cm3)
    """
    _name = "pdp.stone.type"
    _description = "Stone Type"
    # _table = "stone_types"
    # _auto  = False
    # _rec_name = "type"

    code        = fields.Char(string="Code", readonly=False)
    name        = fields.Char(string="Name", readonly=False)
    density     = fields.Float(string="Density (g/cm³)", readonly=False)
    category_code = fields.Many2one(
        comodel_name="pdp.stone.category",
        string="Category",
        readonly=False,
    )

