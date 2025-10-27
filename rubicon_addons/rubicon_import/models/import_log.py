from odoo import models, fields

class ImportLog(models.Model):
    _name = 'rubicon.import.log'
    _description = 'Rubicon Import Log'
    _order = 'start_at desc'

    name = fields.Char(required=True, default='Pictures Import')
    import_type = fields.Selection([
        ('pictures', 'Pictures'),
        ('products', 'Products'),
        ('stones', 'Stones'),
    ], required=True, default='pictures')

    start_at = fields.Datetime(required=True, default=fields.Datetime.now)
    end_at = fields.Datetime()
    status = fields.Selection([
        ('running','Running'),
        ('done','Done'),
        ('error','Error'),
    ], default='running', required=True, index=True)

    total_found = fields.Integer()
    created = fields.Integer()
    updated = fields.Integer()
    skipped = fields.Integer()
    not_found = fields.Integer()
    errors = fields.Text()

    line_ids = fields.One2many('rubicon.import.log.line', 'log_id', string='Lines')

class ImportLogLine(models.Model):
    _name = 'rubicon.import.log.line'
    _description = 'Rubicon Import Log Line'
    _order = 'id desc'

    log_id = fields.Many2one('rubicon.import.log', required=True, ondelete='cascade', index=True)
    filename = fields.Char()
    model_code = fields.Char()
    checksum = fields.Char()
    action = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('skip', 'Skip'),
        ('not_found', 'Not Found'),
        ('error', 'Error'),
    ], index=True)
    message = fields.Char()
    picture_id = fields.Many2one('pdp.picture')
