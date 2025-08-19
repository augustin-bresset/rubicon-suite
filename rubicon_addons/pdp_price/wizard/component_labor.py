from odoo import models, fields, api

class PriceLabor(models.TransientModel):
    _name = 'pdp.price.labor'
    _description = 'Labor Price Component'
    _inherit="pdp.price.component"

    @api.model        
    def compute(self, *, product, margin, currency, date):
        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        LaborCostModel = self.env['pdp.labor.cost.model'].with_context(clean_ctx)
        LaborCostProduct = self.env['pdp.labor.cost.product'].with_context(clean_ctx)
        LaborMargin = self.env['pdp.margin.labor'].with_context(clean_ctx)

        total_cost = total_margin = 0.0
        for labor in self.env['pdp.labor.type'].search([]):            

            # Cost model
            cost_model_id = LaborCostModel.search([
                ('model_id', '=', product.model_id.id),
                ('labor_id', '=', labor.id)
            ], limit=1)
            
            # Cost Product
            cost_product_id = LaborCostProduct.search([
                ('product_id', '=', product.id),
                ('labor_id', '=', labor.id)
            ], limit=1)
            
            if not cost_product_id and not cost_model_id:
                continue
            cost = 0.0
            if cost_model_id:
                model_curr = cost_model_id.currency_id or currency
                cost_model = self._convert(cost_model_id.cost or 0.0, model_curr, currency, date)

            if cost_product_id:               
                product_curr = cost_product_id.currency_id or currency
                cost_product = self._convert(cost_product_id.cost or 0.0, product_curr, currency, date)
                        
                if not cost_product > 0.0 and cost_model:
                    cost = cost_model
                    
            if cost == 0.0:
                cost = cost_product
            total_cost += cost
            
            rate = 1.0
            if margin:
                margin_id = LaborMargin.search([
                    ('margin_id', '=', margin.id),
                    ('labor_id', '=', labor.id),
                ], limit=1)
                rate = margin_id.rate or 1.0
            total_margin += (rate - 1.0) * cost

        return self._payload('labor', total_cost, total_margin, currency)