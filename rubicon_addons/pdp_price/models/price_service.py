from odoo import models, fields, api


class PdpPriceService(models.AbstractModel):
    """
    Price Computation Service.
    Reusable by API, Cron, OWL, Reports.
    """
    _name = 'pdp.price.service'
    _description = 'PDP Price Computation Service'

    @api.model
    def compute_product_price(self, product, margin=None, currency=None, date=None, purity_id=None):
        """
        Compute price breakdown for a product.
        
        Args:
            product: pdp.product record
            margin: pdp.margin record (optional)
            currency: res.currency record (optional)
            date: date for pricing (optional)
        
        Returns:
            dict with 'lines', 'totals', 'currency' keys
        """
        if not product:
            return {'error': 'Product required'}

        margin = margin or self.env['pdp.margin'].search([], limit=1)
        currency = currency or self.env.company.currency_id
        date = date or fields.Date.context_today(self)
        purity = self.env['pdp.metal.purity'].browse(purity_id) if purity_id else None

        # Price components to compute
        components = [
            ('pdp.price.stone', 'stone', 'Stones'),
            ('pdp.price.metal', 'metal', 'Metal'),
            ('pdp.price.conv',  'conv',  'Metal Conv'),
            ('pdp.price.labor', 'labor', 'Labor'),
            ('pdp.price.addon', 'addon', 'Addons'),
            ('pdp.price.part', 'part', 'Parts'),
        ]

        lines = []
        total_cost = 0.0
        total_margin = 0.0
        total_price = 0.0

        all_warnings = []

        for model_name, code, label in components:
            comp_model = self.env.get(model_name)
            if comp_model is None:
                continue

            try:
                extra = {'purity': purity} if model_name in ('pdp.price.metal', 'pdp.price.conv') else {}
                payload = comp_model.compute(
                    product=product,
                    margin=margin,
                    currency=currency,
                    date=date,
                    **extra,
                )
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.exception("Error computing %s for product %s", label, product.code)
                payload = {'cost': 0.0, 'margin': 0.0, 'price': 0.0, 'warnings': [f'Error computing {label}: {e}']}

            c_cost = payload.get('cost', 0.0)
            c_margin = payload.get('margin', 0.0)
            c_price = payload.get('price', 0.0)
            c_warnings = payload.get('warnings', [])
            
            if c_warnings:
                all_warnings.extend(c_warnings)

            lines.append({
                'type': code,
                'label': label,
                'cost': c_cost,
                'margin': c_margin,
                'price': c_price,
            })

            total_cost += c_cost
            total_margin += c_margin
            total_price += c_price

        return {
            'currency': {
                'id': currency.id,
                'symbol': currency.symbol,
                'rate': currency.rate or 1.0,
            },
            'lines': lines,
            'warnings': all_warnings,
            'totals': {
                'cost': currency.round(total_cost),
                'margin': currency.round(total_margin),
                'price': currency.round(total_price),
            }
        }

    @api.model
    def compute_price_by_ids(self, product_id, margin_id, currency_id, purity_id=None):
        """Entry point for JS/OWL: converts raw IDs to records then delegates."""
        product = self.env['pdp.product'].browse(int(product_id))
        if not product.exists():
            return {'error': 'Product not found'}
        margin = self.env['pdp.margin'].browse(int(margin_id)) if margin_id else None
        currency = self.env['res.currency'].browse(int(currency_id))
        return self.compute_product_price(product, margin, currency, purity_id=purity_id)
