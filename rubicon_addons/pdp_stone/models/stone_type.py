from odoo import models, fields


class StoneType(models.Model):
    """
    :note::
     The density was written in reference of the quartz. (2.65gm/cm3)
    """
    _name = "pdp.stone.type"
    _description = "Stone Type"
    _rec_name = "code"
    

    code        = fields.Char(string="Code", size=5, required=True)
    name        = fields.Char(string="Name", size=20, required=True)
    density     = fields.Float(string="Density (g/cm³)")
    category_code = fields.Many2one(
        comodel_name="pdp.stone.category",
        string="Category",
    )

