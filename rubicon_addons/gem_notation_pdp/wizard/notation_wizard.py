from odoo import models, fields


class NotationWizard(models.TransientModel):
    """Add the product-verification mode to the notation wizard."""
    _inherit = 'gem.notation.wizard'

    mode = fields.Selection(selection_add=[('product', 'Verify a product')],
                            ondelete={'product': 'set default'})
    product_id = fields.Many2one('pdp.product', string='Product')

    def _run_lines(self):
        if self.mode != 'product':
            return super()._run_lines()
        if not self.product_id:
            return ['Pick a product first.']
        verdict = self.env['gem.notation'].verify_product(
            self.product_id.id, self.code or '')
        lines = [f"Expected: {verdict['expected'] or '(none)'}",
                 f"Given:    {verdict['given'] or '(none)'}",
                 'Coherent.' if verdict['ok'] else 'NOT coherent:']
        lines.extend(f"  - {p}" for p in verdict['problems'])
        return lines
