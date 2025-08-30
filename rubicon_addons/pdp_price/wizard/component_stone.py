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

        total_cost = total_margin = 0.0
        
        type_ids = set(lines.mapped('stone_id.type_id').ids)
        rate_by_type = {}
        MarginStone = self.env['pdp.margin.stone'].with_context(clean_ctx)
        MarginStoneConditional = self.env['pdp.margin.stone.conditional'].with_context(clean_ctx)

        if margin and type_ids:
            mlines = MarginStone.search([
                ('margin_id', '=', margin.id),
                ('stone_type_id', 'in', list(type_ids)),
            ])
            rate_by_type = {ml.stone_type_id.id: (ml.rate or 1.0) for ml in mlines}

        for line in lines:
            stone = line.stone_id
            if not stone:
                continue
            
            from_cur = stone.currency_id or currency
            unit_cost = self._convert(stone.cost or 0.0, from_cur, currency, date)
            cost = unit_cost * (line.pieces or 1.0)
            total_cost += cost
            
            # Conditional margin
            rate = 0.0
            if margin:
                conditional_margin = MarginStoneConditional.search([
                    ('margin_id', '=', margin.id),
                    ('stone_cat_id', '=', stone.type_id.category_id.id)
                ])
                comparative_cost = self._convert(
                    conditional_margin.comparative_cost,
                    conditional_margin.currency_id or currency,
                    currency,
                    date
                    )
                if conditional_margin.use_operator(cost, comparative_cost, conditional_margin.operator[0]):
                    rate = conditional_margin.rate 
                    
            if rate == 0.0:
                stype_id = stone.type_id.id if stone.type_id else False
                rate = rate_by_type.get(stype_id, 1.0)
            margin_val = (rate - 1.0) * cost
            total_margin += margin_val

        return self._payload('stone', total_cost, total_margin, currency)

