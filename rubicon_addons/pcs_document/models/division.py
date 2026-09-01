from odoo import models, fields


class PcsDivision(models.Model):
    """The real workshop organisation, from the audit process diagram:
    Stone Department, Metal Department, Assembly Department, and the
    transverse Quality Controller. Each pcs.department (a section of the
    flow) belongs to exactly one division; flow-less states (Cancel,
    Melting, Office...) belong to none.

    Distinct from pcs.dept.group, which is the legacy software grouping
    that drives the prod/stone tracks and PBarcode prefixes.
    """
    _name = 'pcs.division'
    _description = 'PCS Workshop Division'
    _rec_name = 'name'
    _order = 'sequence, code'

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The division code must be unique.'),
    ]

    code = fields.Char(string='ID', required=True, index=True)
    name = fields.Char(string='Division', required=True)
    sequence = fields.Integer(default=10)
    department_ids = fields.One2many(
        'pcs.department', 'division_id', string='Sections')
