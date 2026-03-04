from odoo import models, api

class PricePart(models.TransientModel):
    _name = 'pdp.price.part'
    _description = 'Part Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        product_parts = self.env['pdp.product.part'].with_context(clean_ctx).search([
            ('product_id', '=', product.id)
        ])

        if not product_parts:
            return self._payload('part', 0.0, 0.0, currency)

        metal_purity = self.env['pdp.product.model.metal'].with_context(clean_ctx).search([
            ('model_id', '=', product.model_id.id),
            ('metal_version', '=', product.metal),
        ], limit=1).purity_id

        if not metal_purity:
            metal_purity = self.env['pdp.metal.purity'].search([('code', '=', '18K')], limit=1)

        # --- Pre-fetch all part costs in 1 bulk query ---
        part_ids = product_parts.mapped('part_id').ids
        part_costs = self.env['pdp.part.cost'].with_context(clean_ctx).search([
            ('part_id', 'in', part_ids),
            ('purity_id', '=', metal_purity.id),
        ])
        cost_by_part = {r.part_id.id: r for r in part_costs}

        # --- Pre-fetch margin rate once (not per part) ---
        margin_rate = 1.0
        if margin:
            mline = self.env['pdp.margin.part'].with_context(clean_ctx).search([
                ('margin_id', '=', margin.id),
            ], limit=1)
            margin_rate = mline.rate or 1.0

        total_cost = total_margin = 0.0

        for pp in product_parts:
            part_cost = cost_by_part.get(pp.part_id.id)
            if not part_cost:
                continue

            from_cur = part_cost.currency_id or currency
            unit_cost = self._convert(part_cost.cost or 0.0, from_cur, currency, date)
            cost = unit_cost * (pp.quantity or 1.0)
            total_cost += cost
            total_margin += (margin_rate - 1.0) * cost

        return self._payload('part', total_cost, total_margin, currency)
