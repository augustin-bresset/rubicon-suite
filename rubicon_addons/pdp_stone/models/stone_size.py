from odoo import models, fields

class StoneSize(models.Model):
    _name = "pdp.stone.size"
    _description = "Stone Size"
    # _table = "stone_sizes"
    # _auto  = False
    _rec_name = "size"

    size = fields.Char(string="Size", required=True)
    
