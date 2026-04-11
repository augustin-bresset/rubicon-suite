from odoo import models, api

class PriceLabor(models.TransientModel):
    _name = 'pdp.price.labor'
    _description = 'Labor Price Component'
    _inherit = "pdp.price.component"

    @api.model
    def compute(self, *, product, margin, currency, date):
        setting_pl, labor_pl = self.compute_split(product=product, margin=margin, currency=currency, date=date)
        combined_cost = setting_pl['cost'] + labor_pl['cost']
        combined_margin = setting_pl['margin'] + labor_pl['margin']
        return self._payload('labor', combined_cost, combined_margin, currency)

    @api.model
    def compute_split(self, *, product, margin, currency, date):
        """Return (setting_payload, labor_payload) as two separate dicts."""
        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        # SET (setting) is computed from stone lines, not from labor cost tables
        set_type = self.env['pdp.labor.type'].search([('code', '=', 'SET')], limit=1)

        # --- Pre-fetch all relevant costs in 2 bulk queries ---
        model_lines = self.env['pdp.labor.cost.model'].with_context(clean_ctx).search([
            ('model_id', '=', product.model_id.id)
        ])
        model_cost_by_labor = {r.labor_id.id: r for r in model_lines}

        product_lines = self.env['pdp.labor.cost.product'].with_context(clean_ctx).search([
            ('product_id', '=', product.id)
        ])
        product_cost_by_labor = {r.labor_id.id: r for r in product_lines}

        all_labor_ids = set(model_cost_by_labor) | set(product_cost_by_labor)
        has_setting = bool(set_type and product.stone_composition_id)

        # --- Pre-fetch margin rates (include SET even if not in cost tables) ---
        margin_rate_by_labor = {}
        if margin and (all_labor_ids or has_setting):
            margin_labor_ids = all_labor_ids | ({set_type.id} if set_type else set())
            mlines = self.env['pdp.margin.labor'].with_context(clean_ctx).search([
                ('margin_id', '=', margin.id),
                ('labor_id', 'in', list(margin_labor_ids)),
            ])
            margin_rate_by_labor = {r.labor_id.id: (r.rate or 1.0) for r in mlines}

        # --- Setting cost: sum from stone lines ---
        setting_cost = setting_margin = 0.0
        if has_setting:
            stone_lines = self.env['pdp.product.stone'].with_context(clean_ctx).search([
                ('composition_id', '=', product.stone_composition_id.id)
            ])
            for sl in stone_lines:
                unit = sl.setting or 0.0
                if unit > 0.0:
                    from_cur = (sl.setting_type_id.currency_id
                                if sl.setting_type_id and sl.setting_type_id.currency_id
                                else currency)
                    setting_cost += self._convert(unit, from_cur, currency, date) * (sl.pieces or 1)
            if setting_cost:
                set_rate = margin_rate_by_labor.get(set_type.id, 1.0)
                setting_margin = (set_rate - 1.0) * setting_cost

        # --- Regular labor cost (exclude SET to avoid double-counting) ---
        all_labor_ids.discard(set_type.id if set_type else None)
        labor_cost = labor_margin = 0.0
        for labor_id in all_labor_ids:
            model_line = model_cost_by_labor.get(labor_id)
            product_line = product_cost_by_labor.get(labor_id)

            model_c = self._convert(model_line.cost, model_line.currency_id, currency, date) if model_line else 0.0
            product_c = self._convert(product_line.cost, product_line.currency_id, currency, date) if product_line else 0.0

            cost = product_c if product_c > 0.0 else model_c
            labor_cost += cost
            labor_margin += (margin_rate_by_labor.get(labor_id, 1.0) - 1.0) * cost

        setting_payload = self._payload('setting', setting_cost, setting_margin, currency)
        labor_payload = self._payload('labor', labor_cost, labor_margin, currency)
        return setting_payload, labor_payload
