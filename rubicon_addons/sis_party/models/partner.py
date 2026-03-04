from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # SIS-specific fields (everything else is native res.partner)
    sis_code = fields.Char('SIS Code', index=True, help='Legacy SIS customer code (e.g. EMA, BAL)')
    sis_group = fields.Char('SIS Group')
    margin_id = fields.Many2one('pdp.margin', string='Margin')
    sis_pay_term_id = fields.Many2one('sis.pay.term', string='SIS Payment Term')
    sis_ship_method_id = fields.Many2one('sis.shipper', string='Default Ship Method')
    sis_ship_fedex_acc = fields.Char('FedEx Account')
    sis_ship_stamp = fields.Text('Stamp')
    sis_account = fields.Char('SIS Account')
