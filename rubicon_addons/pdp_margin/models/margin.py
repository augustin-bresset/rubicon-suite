from odoo import fields, models


class Margin(models.Model):
    _name="pdp.margin"
    _description="Margin Name"
    _rec_name = "code"
    
    code = fields.Char(string="Margin Code", required=True, index=True)
    name = fields.Char(string="Margin Name", required=True)
    
    