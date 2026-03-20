from odoo import models, fields


class ResPartnerPhone(models.Model):
    _name = 'res.partner.phone'
    _description = 'Additional Phone Numbers'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
    name = fields.Char('Label', help='E.g., Fax, Phone 2, Mobile')
    phone = fields.Char('Phone Number', required=True)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    # Free-text bank name + address (SIS had unstructured text, not structured res.bank)
    sis_bank_name    = fields.Char('Bank Name')
    sis_bank_address = fields.Text('Bank Address')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # SIS-specific fields (everything else is native res.partner)
    sis_code = fields.Char('SIS Code', index=True, help='Legacy SIS customer code (e.g. EMA, BAL)')
    sis_contact = fields.Char('SIS Contact')
    sis_group = fields.Char('SIS Group')
    
    # Customer / Vendor booleans
    sis_is_customer = fields.Boolean('Is a Customer', default=False)
    sis_is_vendor = fields.Boolean('Is a Vendor', default=False)

    sis_phone_ids = fields.One2many('res.partner.phone', 'partner_id', string='Additional Phones')

    # Sales Defaults
    margin_id = fields.Many2one('pdp.margin', string='Margin')
    sis_pay_term_id = fields.Many2one('sis.pay.term', string='SIS Payment Term')
    sis_account = fields.Char('SIS Account')
    
    # Purchase Defaults
    sis_vendor_account = fields.Char('Vendor Account')
    sis_vendor_pay_term_id = fields.Many2one('sis.pay.term', string='Vendor Payment Term')

    # Shipment Info
    sis_ship_address = fields.Text('Shipment Address')
    sis_ship_city = fields.Char('Ship City')
    sis_ship_state = fields.Char('Ship State')
    sis_ship_zip = fields.Char('Ship Zip')
    sis_ship_country_id = fields.Many2one('res.country', string='Shipment Country')
    sis_ship_method_id = fields.Many2one('sis.shipper', string='Default Method Courier')
    sis_ship_fedex_acc = fields.Char('FedEx Account')
    sis_ship_stamp = fields.Text('Stamp')
