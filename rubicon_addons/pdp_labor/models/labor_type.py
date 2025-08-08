from odoo import models, fields

class LaborTypes(models.Model):
    _name = 'pdp.labor.type'
    _description = 'Labor Types'
    _rec_name = 'code'

    code = fields.Char(string='Labor Types Code', required=True, size=3)
    name = fields.Char(string='Labor Types Name', required=True, size=50)

