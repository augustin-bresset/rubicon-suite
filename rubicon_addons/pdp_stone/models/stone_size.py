from odoo import models, fields

class StoneSize(models.Model):
    _name = "pdp.stone.size"
    _description = "Stone Size"
    _rec_name = "name"

    name = fields.Char(string="Size", required=True, index=True)    
    
