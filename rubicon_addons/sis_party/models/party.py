from odoo import models, fields, api


class SisParty(models.Model):
    _name = 'sis.party'
    _description = 'SIS Party (Client/Vendor)'
    _rec_name = 'company'

    # Required
    company = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    # Classification
    is_company = fields.Boolean(default=False)
    contact_type = fields.Selection([
        ('company', 'Company'),
        ('individual', 'Individual'),
    ], string='Contact Type', default='company')
    customer_rank = fields.Integer(default=0)
    supplier_rank = fields.Integer(default=0)

    # Parent/Child (Company ↔ Contact)
    parent_id = fields.Many2one('sis.party', string='Company', index=True,
                                domain="[('contact_type', '=', 'company')]")
    child_ids = fields.One2many('sis.party', 'parent_id', string='Contacts')

    # General
    contact = fields.Char()
    title = fields.Char()

    # Address
    address = fields.Char()
    city = fields.Char()
    state = fields.Char()
    zip = fields.Char()
    country_id = fields.Many2one('sis.country', string='Country')

    # Communication
    phone = fields.Char()
    email = fields.Char()
    fax = fields.Char()
    homepage = fields.Char()
    notes = fields.Text()

    # Groups
    group_code = fields.Char(string='Group')

    # Defaults
    is_vendor = fields.Boolean(default=False)
    margin_id = fields.Many2one('pdp.margin', string='Margin')
    pay_term_id = fields.Many2one('sis.pay.term', string='Payment Term')
    account = fields.Char()

    # Shipment Info
    ship_address = fields.Char(string='Ship Address')
    ship_city = fields.Char(string='Ship City')
    ship_state = fields.Char(string='Ship State')
    ship_zip = fields.Char(string='Ship Zip')
    ship_country_id = fields.Many2one('sis.country', string='Ship Country')
    ship_method_id = fields.Many2one('sis.shipper', string='Default Ship Method')
    ship_fedex_acc = fields.Char(string='FedEx Account')
    ship_stamp = fields.Text(string='Stamp')

    # Bank Info
    bank_name = fields.Char(string='Bank Name')
    bank_address = fields.Text(string='Bank Address')
    bank_acc_name = fields.Char(string='Account Name')
    bank_acc_no = fields.Char(string='Account No.')
