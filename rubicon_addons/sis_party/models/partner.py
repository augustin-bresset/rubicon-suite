from odoo import models, fields


class ResPartnerPhone(models.Model):
    _name = 'res.partner.phone'
    _description = 'Additional Phone Numbers'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    name = fields.Char('Label')
    phone = fields.Char('Phone Number', required=True)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    sis_bank_name    = fields.Char('Bank Name')
    sis_bank_address = fields.Text('Bank Address')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sis_code    = fields.Char('SIS Code', index=True)
    sis_group   = fields.Char('SIS Group')

    sis_is_customer = fields.Boolean('Is a Customer', default=False)
    sis_is_vendor   = fields.Boolean('Is a Vendor',   default=False)

    sis_phone_ids = fields.One2many('res.partner.phone', 'partner_id', string='Additional Phones')

    margin_id        = fields.Many2one('pdp.margin',  string='Margin')
    sis_pay_term_id  = fields.Many2one('sis.pay.term', string='SIS Payment Term')
    sis_account      = fields.Char('SIS Account')

    sis_vendor_account      = fields.Char('Vendor Account')
    sis_vendor_pay_term_id  = fields.Many2one('sis.pay.term', string='Vendor Payment Term')

    # Shipment — only SIS-specific fields without an Odoo equivalent
    sis_ship_method_id  = fields.Many2one('sis.shipper', string='Default Shipping Method')
    sis_ship_fedex_acc  = fields.Char('FedEx Account')
    sis_ship_stamp      = fields.Text('Stamp')
