from odoo import models, fields, api

class PricePart(models.TransientModel):
    _name = 'pdp.price.part'
    _description = 'Part Price Component'
    _inherit = 'pdp.price.component' 

    @api.model
    def compute(self, *, product, margin, currency, date):
        
        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        ProductPart = self.env['pdp.product.part'].with_context(clean_ctx)
        MetalModel = self.env['pdp.product.model.metal'].with_context(clean_ctx)
        PartCost = self.env['pdp.part.cost'].with_context(clean_ctx)
        MarginPart = self.env['pdp.margin.part'].with_context(clean_ctx)
        
        product_part_ids = ProductPart.search([('product_id', '=', product.id)])
        
        if not product_part_ids:
            return self._payload('part', 0.0, 0.0, currency)
        
        metal_purity_id = MetalModel.search([
            ('model_id', '=', product.model_id.id),
            ('metal_version', '=', product.metal),
        ], limit=1).purity_id
        
        if not metal_purity_id:
            metal_purity_id = self.env['pdp.metal.purity'].search([
                ('code', '=', '18K')
            ], limit=1)
        
        total_cost = total_margin = 0.0
        
        for product_part_id in product_part_ids:
            part_id = product_part_id.part_id
            part_cost_id = PartCost.search([
                ('part_id', '=', part_id.id),
                ('purity_id', '=', metal_purity_id.id),
            ], limit=1)
            
            if not part_cost_id:
                continue
            
            from_cur = part_cost_id.currency_id or currency
            unit_cost = self._convert(part_cost_id.cost or 0.0, from_cur, currency, date)
            cost = unit_cost * (product_part_id.quantity or 1.0)
            total_cost += cost
            
            rate = 1.0
            if margin:
                margin_rate_id = MarginPart.search([
                    ('margin_id', '=', margin.id),
                ], limit=1)
                rate = margin_rate_id.rate or 1.0
            total_margin += (rate - 1.0) * cost
                
        return self._payload('part', total_cost, total_margin, currency)

