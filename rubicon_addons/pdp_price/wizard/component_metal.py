# wizard/component_metal.py
from odoo import models, api

OZ_TO_G = 31.1034768

class PriceMetal(models.TransientModel):
    _name = 'pdp.price.metal'
    _description = 'Metal Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):

        if not product.model_id:
            return self._payload('metal', 0.0, 0.0, currency)

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}
        ModelMetal = self.env['pdp.product.model.metal'].with_context(clean_ctx)
        model_metal = ModelMetal.search([
            ('model_id', '=', product.model_id.id),
            ('metal_version', '=', product.metal),
        ], limit=1)
        if not model_metal:
            return self._payload('metal', 0.0, 0.0, currency)
        
        if margin:
            Marge = self.env['pdp.margin.metal'].with_context(clean_ctx)
            margin_id = Marge.search([
                ('margin_id', '=', margin.id),
                # ('metal_id', 'in', [k[0] for k in key_set]),
                ('metal_purity_id', '=', model_metal.purity_id.id),
            ], limit=1)
            
            rate = margin_id.rate or 1.0

        total_cost = total_margin = 0.0
            
        # Need USD for price computation
        try:
            usd = self.env.ref('base.USD')
        except Exception:
            usd = currency  # au pire aucune conversion

        cost_per_gram_usd = 0.0
        
        # Check cost method
        cost_method = model_metal.metal_id.cost_method
        
        if cost_method == 'market' and model_metal.metal_id.market_metal_id:
            # Market Cost Strategy
            market_metal = model_metal.metal_id.market_metal_id
            
            # Find latest price
            MarketPrice = self.env['pdp.market.price']
            price_rec = MarketPrice.search([
                ('metal_id', '=', market_metal.id),
                ('date', '<=', date or fields.Date.context_today(self))
            ], order='date desc', limit=1)
            
            if price_rec:
                # Convert price to USD
                market_price_usd = self._convert(price_rec.price, price_rec.currency_id, usd, date)
                
                # Convert unit to gram
                if market_metal.base_unit == 'troy_oz':
                    cost_per_gram_usd = market_price_usd / OZ_TO_G
                else: # gram
                    cost_per_gram_usd = market_price_usd
            else:
                # Fallback to fixed cost if no market price found? Or 0?
                # For now let's fall back to 0 but maybe we should log a warning (future step)
                pass 
                
        else:
            # Fixed Cost Strategy (default)
            # cost is per ounce in metal definition
            fixed_cost_usd = self._convert(model_metal.metal_id.cost or 0.0, model_metal.metal_id.currency_id, usd, date)
            cost_per_gram_usd = fixed_cost_usd / OZ_TO_G


        grams = model_metal.weight or 0.0
        usd_cost = cost_per_gram_usd * grams
        total_cost = self._convert(usd_cost, usd, currency, date)
        if margin:
            total_margin += (rate - 1.0) * total_cost

        return self._payload('metal', total_cost, total_margin, currency)
