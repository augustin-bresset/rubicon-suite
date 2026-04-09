# wizard/component_conv.py
from odoo import models, api

OZ_TO_G = 31.1034768


class PriceConv(models.TransientModel):
    _name = 'pdp.price.conv'
    _description = 'Metal Conversion Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date, purity=None):
        """
        Metal Conv: cost of casting the product in the actual metal,
        derived from the reference (WG18K) weight and the density/price ratio.

        When product.metal == reference metal code → returns 0 (no conversion needed).
        """
        if not product.model_id:
            return self._payload('conv', 0.0, 0.0, currency)

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        # --- Reference metal (should be WG18K, marked is_reference=True) ---
        ref_metal = self.env['pdp.metal'].with_context(clean_ctx).search(
            [('is_reference', '=', True)], limit=1
        )
        if not ref_metal or not ref_metal.density:
            return self._payload('conv', 0.0, 0.0, currency)

        # --- If the product uses the reference metal itself → no conversion ---
        if product.metal == ref_metal.code:
            return self._payload('conv', 0.0, 0.0, currency)

        # --- Actual metal: look up pdp.metal by code matching product.metal ---
        actual_metal = self.env['pdp.metal'].with_context(clean_ctx).search(
            [('code', '=', product.metal)], limit=1
        )
        if not actual_metal or not actual_metal.density:
            return self._payload('conv', 0.0, 0.0, currency)

        # --- Reference weight: model metal entry for metal_version = ref_metal.code ---
        ModelMetal = self.env['pdp.product.model.metal'].with_context(clean_ctx)
        ref_model_metal = ModelMetal.search([
            ('model_id', '=', product.model_id.id),
            ('metal_version', '=', ref_metal.code),
        ], limit=1)
        if not ref_model_metal:
            return self._payload('conv', 0.0, 0.0, currency)

        weight_ref = ref_model_metal.weight or 0.0
        if weight_ref == 0.0:
            return self._payload('conv', 0.0, 0.0, currency)

        # --- Weight in actual metal (same volume, different density) ---
        density_ratio = actual_metal.density / ref_metal.density
        weight_actual = weight_ref * density_ratio

        # --- Effective purity for actual metal ---
        actual_model_metal = ModelMetal.search([
            ('model_id', '=', product.model_id.id),
            ('metal_version', '=', product.metal),
        ], limit=1)
        stored_purity = (actual_model_metal.purity_id if actual_model_metal
                         else actual_metal.default_purity_id)
        metal_system = actual_metal.purity_system
        if (purity and purity.exists()
                and (not metal_system or purity.purity_system == metal_system)):
            effective_purity = purity
        else:
            effective_purity = stored_purity
        purity_percent = effective_purity.percent if effective_purity else 100.0

        # --- Cost per gram of actual metal in USD ---
        try:
            usd = self.env.ref('base.USD')
        except Exception:
            usd = currency

        cost_per_gram_usd = 0.0
        if actual_metal.cost_method == 'market' and actual_metal.market_metal_id:
            from odoo import fields as odoo_fields
            MarketPrice = self.env['pdp.market.price']
            price_rec = MarketPrice.search([
                ('metal_id', '=', actual_metal.market_metal_id.id),
                ('date', '<=', date or odoo_fields.Date.context_today(self)),
            ], order='date desc', limit=1)
            if price_rec:
                market_price_usd = self._convert(price_rec.price, price_rec.currency_id, usd, date)
                if actual_metal.market_metal_id.base_unit == 'troy_oz':
                    cost_per_gram_usd = market_price_usd / OZ_TO_G
                else:
                    cost_per_gram_usd = market_price_usd
        else:
            cost_per_gram_usd = self._convert(
                actual_metal.cost or 0.0, actual_metal.currency_id, usd, date
            ) / OZ_TO_G

        # pure_grams = alloy_weight × purity_fraction
        pure_grams = weight_actual * (purity_percent / 100.0)
        usd_cost = cost_per_gram_usd * pure_grams
        total_cost = self._convert(usd_cost, usd, currency, date)

        # --- Margin (reuses pdp.margin.metal keyed on purity) ---
        rate = 1.0
        if margin and effective_purity:
            margin_rule = self.env['pdp.margin.metal'].with_context(clean_ctx).search([
                ('margin_id', '=', margin.id),
                ('metal_purity_id', '=', effective_purity.id),
            ], limit=1)
            rate = margin_rule.rate or 1.0
        total_margin = (rate - 1.0) * total_cost

        return self._payload('conv', total_cost, total_margin, currency)
