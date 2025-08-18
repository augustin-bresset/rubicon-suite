from odoo import models, fields

class AddonType(models.Model):
    _name = 'pdp.addon.type'
    _description = 'Addon Type'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True, index=True)
    name = fields.Char(string='Name', required=True)

