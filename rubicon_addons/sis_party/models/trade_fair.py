from odoo import models, fields


class SisTradeFair(models.Model):
    _name = 'sis.trade.fair'
    _description = 'SIS Trade Fair'
    _rec_name = 'name'

    name = fields.Char(required=True)
    city = fields.Char()
    country_id = fields.Many2one('res.country', string='Country')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
