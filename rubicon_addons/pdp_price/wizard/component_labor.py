from odoo import models, api

class PriceLabor(models.TransientModel):
    _name = 'pdp.price.labor'
    _description = 'Labor Price Component'
    _inherit = "pdp.price.component"

    @api.model
    def compute(self, *, product, margin, currency, date):
        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        # --- Pre-fetch all relevant costs in 3 bulk queries ---
        model_lines = self.env['pdp.labor.cost.model'].with_context(clean_ctx).search([
            ('model_id', '=', product.model_id.id)
        ])
        model_cost_by_labor = {r.labor_id.id: r for r in model_lines}

        product_lines = self.env['pdp.labor.cost.product'].with_context(clean_ctx).search([
            ('product_id', '=', product.id)
        ])
        product_cost_by_labor = {r.labor_id.id: r for r in product_lines}

        # Only process labor types that have at least one cost entry
        all_labor_ids = set(model_cost_by_labor) | set(product_cost_by_labor)
        if not all_labor_ids:
            return self._payload('labor', 0.0, 0.0, currency)

        # --- Pre-fetch all margin labor rates in 1 query ---
        margin_rate_by_labor = {}
        if margin:
            mlines = self.env['pdp.margin.labor'].with_context(clean_ctx).search([
                ('margin_id', '=', margin.id),
                ('labor_id', 'in', list(all_labor_ids)),
            ])
            margin_rate_by_labor = {r.labor_id.id: (r.rate or 1.0) for r in mlines}

        total_cost = total_margin = 0.0

        for labor_id in all_labor_ids:
            model_line = model_cost_by_labor.get(labor_id)
            product_line = product_cost_by_labor.get(labor_id)

            model_cost = self._convert(model_line.cost, model_line.currency_id, currency, date) if model_line else 0.0
            product_cost = self._convert(product_line.cost, product_line.currency_id, currency, date) if product_line else 0.0

            # Priority: product_cost > 0 → use it; else fallback to model_cost
            cost = product_cost if product_cost > 0.0 else model_cost
            total_cost += cost

            rate = margin_rate_by_labor.get(labor_id, 1.0)
            total_margin += (rate - 1.0) * cost

        return self._payload('labor', total_cost, total_margin, currency)
