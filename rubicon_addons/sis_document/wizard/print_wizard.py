from odoo import api, models, fields


class SisDocumentPrintWizard(models.TransientModel):
    """Options of the backend Print action.

    The OWL workspace has its own print dialog; this wizard offers the same
    choices (layout, markup, design-code notation, pictures) to users
    printing from the regular list and form views.
    """
    _name = 'sis.document.print.wizard'
    _description = 'SIS Document Print Options'

    document_ids = fields.Many2many('sis.document', string='Documents',
                                    required=True)
    print_type = fields.Selection([
        ('with_weights', 'With Weights'),
        ('tax_invoice', 'Tax Invoice'),
        ('proforma', 'Pro-forma Invoice'),
        ('normal', 'Normal'),
        ('compressed', 'With Weights Compressed'),
    ], string='Layout', default='with_weights', required=True)
    print_markup = fields.Float(string='Markup %')
    print_notation = fields.Selection([
        ('legacy', 'Historical'),
        ('alternative', 'Alternative'),
        ('both', 'Both'),
    ], string='Design Codes', default='legacy', required=True)
    print_pictures = fields.Boolean(string='Include Pictures')

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if ('document_ids' in fields_list
                and self.env.context.get('active_model') == 'sis.document'):
            vals['document_ids'] = [(6, 0, self.env.context.get('active_ids', []))]
        return vals

    def action_print(self):
        self.ensure_one()
        report = self.env.ref('sis_document.action_report_sis_document')
        return report.with_context(
            print_type=self.print_type,
            print_markup=self.print_markup,
            print_notation=self.print_notation,
            print_pictures=self.print_pictures,
        ).report_action(self.document_ids)
