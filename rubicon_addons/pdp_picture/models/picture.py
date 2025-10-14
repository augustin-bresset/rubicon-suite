from odoo import models, fields, api

class Picture(models.Model):
    _name = 'pdp.picture'
    _table = 'pdp_pictures'
    _description = 'Picture linked to a PDP model'
    _rec_name = 'name'
    _order = 'sequence, id'

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    # Legacy / import reference (e.g., JMS code or filename stem)
    code = fields.Char(string='Legacy Code', index=True)

    name = fields.Char(string='Name', required=True)
    kind = fields.Selection(
        selection=[
            ('sketch', 'Sketch'),
            ('snapshot', 'Snapshot'),
            ('render', 'Render'),
            ('other', 'Other'),
        ],
        string='Type',
        default='sketch',
        index=True,
        required=True,
    )
    sequence = fields.Integer(default=10)

    # Actual image payload -> stored in filestore thanks to attachment=True
    image = fields.Binary(string='Image', attachment=True, required=True)
    filename = fields.Char(string='Filename')
    checksum = fields.Char(string='Checksum', index=True)
    active = fields.Boolean(default=True)

    # Link to PDP model
    model_id = fields.Many2one(
        'pdp.product.model',
        string='Model',
        ondelete='set null',
        index=True,
    )

    # Convenience: mirror the model code to help with imports/filtering
    model_code = fields.Char(related='model_id.code', store=True, index=True)

    # Optional: auto-name from filename if not set
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            fname = vals.get('filename') or vals.get('code') or 'Picture'
            vals['name'] = fname
        return super().create(vals)
