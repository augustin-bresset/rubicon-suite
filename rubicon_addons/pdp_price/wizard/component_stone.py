# wizard/component_stone.py
from odoo import models, api

class PriceStone(models.TransientModel):
    _name = 'pdp.price.stone'
    _description = 'Stone Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):

        if not product.stone_composition_id:
            return self._payload('stone', 0.0, 0.0, currency)

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        StoneLine = self.env['pdp.product.stone'].with_context(clean_ctx)
        lines = StoneLine.search([('composition_id', '=', product.stone_composition_id.id)])

        if not lines:
            return self._payload('stone', 0.0, 0.0, currency)

        # --- Pre-fetch to warm Odoo's ORM cache (avoids N+1 on field access) ---
        stones = lines.mapped('stone_id')
        stones.mapped('type_id').mapped('category_id')

        # --- Pre-fetch normal margin rates by stone type (1 query) ---
        type_ids = stones.mapped('type_id').ids
        rate_by_type = {}
        if margin and type_ids:
            mlines = self.env['pdp.margin.stone'].with_context(clean_ctx).search([
                ('margin_id', '=', margin.id),
                ('stone_type_id', 'in', type_ids),
            ])
            rate_by_type = {ml.stone_type_id.id: (ml.rate or 1.0) for ml in mlines}

        # --- Pre-fetch conditional margins by category (1 query, not 1 per stone) ---
        cond_by_cat = {}
        if margin:
            cat_ids = stones.mapped('type_id.category_id').ids
            if cat_ids:
                cond_lines = self.env['pdp.margin.stone.conditional'].with_context(clean_ctx).search([
                    ('margin_id', '=', margin.id),
                    ('stone_cat_id', 'in', cat_ids),
                ])
                cond_by_cat = {r.stone_cat_id.id: r for r in cond_lines}

        total_cost = total_margin = 0.0
        warnings = []

        for line in lines:
            stone = line.stone_id
            if not stone:
                continue

            from_cur = stone.currency_id or currency
            raw_cost = stone.cost or 0.0
            if raw_cost <= 0.0:
                warnings.append(f"Stone {stone.code} has no cost defined.")

            unit_cost = self._convert(raw_cost, from_cur, currency, date)
            cost = unit_cost * (line.pieces or 1.0)
            total_cost += cost

            # Conditional margin — dict lookup (no SQL)
            rate = 0.0
            if margin:
                cat_id = stone.type_id.category_id.id if stone.type_id and stone.type_id.category_id else False
                cond = cond_by_cat.get(cat_id)
                if cond:
                    comparative_cost = self._convert(
                        cond.comparative_cost,
                        cond.currency_id or currency,
                        currency,
                        date,
                    )
                    if cond.use_operator(cost, comparative_cost, cond.operator):
                        rate = cond.rate

            if rate == 0.0:
                stype_id = stone.type_id.id if stone.type_id else False
                rate = rate_by_type.get(stype_id, 1.0)

            total_margin += (rate - 1.0) * cost

        return self._payload('stone', total_cost, total_margin, currency, warnings=warnings)
