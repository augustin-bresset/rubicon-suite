from odoo import models, fields


class PcsClearance(models.Model):
    """End-of-period clearance: outstanding weights per employee."""
    _name = 'pcs.clearance'
    _description = 'PCS Clearance'
    _order = 'date desc, id desc'

    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    prod_line_ids = fields.One2many(
        'pcs.clearance.prod.line', 'clearance_id', string='Prod Lines')
    ssp_line_ids = fields.One2many(
        'pcs.clearance.ssp.line', 'clearance_id', string='SSP Lines')


class PcsClearanceProdLine(models.Model):
    _name = 'pcs.clearance.prod.line'
    _description = 'PCS Clearance Production Line'

    clearance_id = fields.Many2one(
        'pcs.clearance', required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one('pcs.employee', string='Employee')
    barcode_id = fields.Many2one('pcs.barcode', string='Barcode')
    design = fields.Char(related='barcode_id.design', string='Design')
    purity = fields.Char(related='barcode_id.purity', string='Purity')
    issue_weight = fields.Float(string='Issue Wht.', digits=(10, 3))
    rm_weight = fields.Float(string='RM Wht.', digits=(10, 3))
    received_weight = fields.Float(string='Rcvd. Wht.', digits=(10, 3))


class PcsClearanceSspLine(models.Model):
    _name = 'pcs.clearance.ssp.line'
    _description = 'PCS Clearance SSP Line'

    clearance_id = fields.Many2one(
        'pcs.clearance', required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one('pcs.employee', string='Employee')
    ssp_id = fields.Many2one('pcs.ssp', string='SSP')
    purity = fields.Char(string='Purity')
    issue_weight = fields.Float(string='Issue Wht.', digits=(10, 3))
    received_weight = fields.Float(string='Rcvd. Wht.', digits=(10, 3))
    date = fields.Date(string='Date', default=fields.Date.context_today)
