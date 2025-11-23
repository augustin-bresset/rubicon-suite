# rubicon_addons/pdp_metal_market/models/metal_service.py
from odoo import models, api, fields

TROY_OZ_TO_G = 31.1034768

class MetalPriceService(models.AbstractModel):
    _name = "pdp.metal.price.service"
    _description = "Spot price computation per day"

    @api.model
    def _spot_record(self, metal, date):
        Price = self.env['pdp.market.price']
        rec = Price.search([('metal_id','=',metal.id), ('date','<=', date)], order="date desc", limit=1)
        return rec

    @api.model
    def get_spot_per_gram(self, metal, date, to_currency):
        """Return price per gram in target currency at the given date."""
        rec = self._spot_record(metal, date)
        if not rec:
            return 0.0
        amount = rec.price
        # base unit normalization
        per_g = amount / (TROY_OZ_TO_G if metal.base_unit == 'troy_oz' else 1.0)
        # currency conversion (base -> target) at date
        return rec.metal_id.base_currency_id._convert(per_g, to_currency, self.env.company, date)

    @api.model
    def get_alloy_price_per_gram(self, variant_code, date, to_currency):
        Alloy = self.env['pdp.metal.alloy']
        alloy = Alloy.search([('variant_code', '=', variant_code)], limit=1)
        if not alloy:
            return 0.0
        total = 0.0
        for line in alloy.line_ids:
            total += (line.ratio or 0.0) * self.get_spot_per_gram(line.metal_id, date, to_currency)
        return total * (alloy.yield_factor or 1.0)

    @api.model
    def get_spot_per_gram_with_purity(self, metal, date, to_currency, purity_percent):
        """Return price per gram in target currency at the given date adjusted by purity percent.
        purity_percent is expected as a value between 0 and 100.
        """
        try:
            p = float(purity_percent)
        except (TypeError, ValueError):
            return 0.0
        if p <= 0.0:
            return 0.0
        if p > 100.0:
            p = 100.0
        base_price = self.get_spot_per_gram(metal, date, to_currency)
        return base_price * (p / 100.0)