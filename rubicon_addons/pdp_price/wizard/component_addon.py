from odoo import fields, models, api

class PriceAddon(models.TransientModel):
    _name="pdp.price.addon"
    _description="Compute Addon Price"
    _inherit="pdp.price.component"


    @api.model
    def compute(self, *, product, margin, currency, date):

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        AddonCost = self.env['pdp.addon.cost'].with_context(clean_ctx)


        groups = AddonCost.read_group(
            domain=[('product_id', '=', product.id)],
            fields=['cost:sum', 'currency_id', 'addon_id'],
            groupby=['addon_id', 'currency_id'],
            lazy=False,
        )
        if not groups:
            return self._payload('addon', 0.0, 0.0, currency)
        
        margin_map = {}
        if margin:
            addon_ids = [g['addon_id'][0] for g in groups if g.get('addon_id')]
            if addon_ids:
                ml = (self.env['pdp.margin.addon']
                      .with_context(clean_ctx)
                      .search([('margin_id', '=', margin.id),
                               ('addon_id', 'in', addon_ids)]))
                margin_map = {r.addon_id.id: (r.rate or 1.0) for r in ml}

        total_cost = 0.0
        total_margin = 0.0
        Currency = self.env['res.currency']


        for g in groups:
            sum_cost = g.get('cost_sum') or 0.0

            if g.get('currency_id'):
                from_cur = Currency.browse(g['currency_id'][0])
            else:
                from_cur = currency  
            cost_in_cur = self._convert(sum_cost, from_cur, currency, date)

            total_cost += cost_in_cur

            addon_id = g['addon_id'][0] if g.get('addon_id') else None
            rate = margin_map.get(addon_id, 1.0)
            total_margin += (rate - 1.0) * cost_in_cur
        

        return self._payload('addon', total_cost, total_margin, currency)