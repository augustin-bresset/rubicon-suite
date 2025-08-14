from odoo import models, fields

class StoneShade(models.Model):
    _name = "pdp.stone.shade"
    _description = "Stone Shade"

    _rec_name = "code"

    code  = fields.Char(string="Code", required=True, index=True)
    shade = fields.Char(string="Shade", required=True)
    
    _sql_constraints = [("name_uniq","unique(shade)","Shade must be unique.")]
