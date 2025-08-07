from odoo import fields, models


class Margin(models.Model):
    _name="pdp.margin"
    _rec_name = "code"
    _description="Margin Name"
    
    code = fields.Char(string="Margin Code", size=5, required=True)
    name = fields.Char(string="Margin Name", size=20, required=True)
    
    