from odoo import field, models


class Margin(models.Model):
    _name="pdp.margin"
    _rec_name = "code"
    
    
    code = field.Char(string="Margin Code", size=5, required=True)
    name = field.Char(string="Margin Name", size=20, required=True)
    over_all_margins = field.Char(digits=(5, 3))
    parts_margin = field.Char(digits=(5, 3))
    labor_margin = field.Char(digits=(5, 3))
    casting_margin = field.Char(digits=(5, 3))
    stone_margin = field.Char(digits=(5, 3))

    