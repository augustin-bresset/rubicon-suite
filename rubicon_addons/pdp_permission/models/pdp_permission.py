from odoo import models, fields, api


class PdpPermission(models.Model):
    """
    Defines individual permissions that can be assigned to roles.
    Example: 'product.read', 'price.update', 'stone.delete'
    """
    _name = 'pdp.permission'
    _description = 'PDP Permission'
    _order = 'category, code'

    code = fields.Char(
        string='Code',
        required=True,
        index=True,
        help='Unique identifier for the permission (e.g., product.read)'
    )
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help='Display name of the permission'
    )
    category = fields.Selection(
        selection=[
            ('product', 'Products'),
            ('price', 'Pricing'),
            ('stone', 'Stones'),
            ('metal', 'Metals'),
            ('labor', 'Labor'),
            ('margin', 'Margins'),
            ('order', 'Orders'),
            ('invoice', 'Invoices'),
            ('stock', 'Stock'),
            ('purchase', 'Purchasing'),
            ('export', 'Export'),
            ('admin', 'Administration'),
        ],
        string='Category',
        required=True,
        help='Category of the permission for grouping'
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed description of what this permission allows'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Permission code must be unique!')
    ]

    def name_get(self):
        return [(rec.id, f"[{rec.code}] {rec.name}") for rec in self]
