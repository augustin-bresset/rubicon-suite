from odoo import models, fields, api


class PdpPriceService(models.AbstractModel):
    """
    Price Computation Service.
    Reusable by API, Cron, OWL, Reports.
    """
    _name = 'pdp.price.service'
    _description = 'PDP Price Computation Service'

    @api.model
    def compute_product_price(self, product, margin=None, currency=None, date=None, purity_id=None, conv_metal_code=None):
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

        import logging
        _logger = logging.getLogger(__name__)

        def _safe_compute(model_name, label, **kwargs):
            comp = self.env.get(model_name)
            if comp is None:
                return {'cost': 0.0, 'margin': 0.0, 'price': 0.0, 'warnings': []}
            try:
                return comp.compute(product=product, margin=margin, currency=currency, date=date, **kwargs)
            except Exception as e:
                _logger.exception("Error computing %s for product %s", label, product.code)
                return {'cost': 0.0, 'margin': 0.0, 'price': 0.0, 'warnings': [f'Error computing {label}: {e}']}

        lines = []
        total_cost = 0.0
        total_margin = 0.0
        total_price = 0.0
        all_warnings = []

        def _add_line(type_code, label, payload):
            nonlocal total_cost, total_margin, total_price
            c_cost = payload.get('cost', 0.0)
            c_margin = payload.get('margin', 0.0)
            c_price = payload.get('price', 0.0)
            warns = payload.get('warnings', [])
            if warns:
                all_warnings.extend(warns)
            lines.append({'type': type_code, 'label': label, 'cost': c_cost, 'margin': c_margin, 'price': c_price})
            total_cost += c_cost
            total_margin += c_margin
            total_price += c_price

        # 1. Metal (metal + conv merged into one line)
        metal_pl = _safe_compute('pdp.price.metal', 'Metal', purity=purity)
        conv_extra = {'purity': purity}
        if conv_metal_code:
            conv_extra['conv_metal_code'] = conv_metal_code
        conv_pl = _safe_compute('pdp.price.conv', 'Metal Conv', **conv_extra)
        _add_line('metal', 'Metal', {
            'cost':     metal_pl.get('cost', 0.0)   + conv_pl.get('cost', 0.0),
            'margin':   metal_pl.get('margin', 0.0) + conv_pl.get('margin', 0.0),
            'price':    metal_pl.get('price', 0.0)  + conv_pl.get('price', 0.0),
            'warnings': metal_pl.get('warnings', []) + conv_pl.get('warnings', []),
        })

        # 2. Stone
        _add_line('stone', 'Stone', _safe_compute('pdp.price.stone', 'Stone'))

        # 3. Setting + 5. Labor — split from labor component
        labor_comp = self.env.get('pdp.price.labor')
        if labor_comp is not None:
            try:
                setting_pl, labor_pl = labor_comp.compute_split(
                    product=product, margin=margin, currency=currency, date=date
                )
            except Exception as e:
                _logger.exception("Error computing Labor for product %s", product.code)
                setting_pl = {'cost': 0.0, 'margin': 0.0, 'price': 0.0, 'warnings': [f'Error computing Setting: {e}']}
                labor_pl   = {'cost': 0.0, 'margin': 0.0, 'price': 0.0, 'warnings': []}
        else:
            setting_pl = labor_pl = {'cost': 0.0, 'margin': 0.0, 'price': 0.0, 'warnings': []}

        _add_line('setting',   'Setting',   setting_pl)

        # 4. Recutting
        _add_line('recutting', 'Recutting', _safe_compute('pdp.price.recutting', 'Recutting'))

        _add_line('labor',     'Labor',     labor_pl)

        # 6. Misc (addons)
        _add_line('misc', 'Misc', _safe_compute('pdp.price.addon', 'Misc'))

        # 7. Parts
        _add_line('parts', 'Parts', _safe_compute('pdp.price.part', 'Parts'))

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
    def compute_price_by_ids(self, product_id, margin_id, currency_id, purity_id=None, conv_metal_code=None):
        """Entry point for JS/OWL: converts raw IDs to records then delegates."""
        product = self.env['pdp.product'].browse(int(product_id))
        if not product.exists():
            return {'error': 'Product not found'}
        margin = self.env['pdp.margin'].browse(int(margin_id)) if margin_id else None
        currency = self.env['res.currency'].browse(int(currency_id))
        return self.compute_product_price(product, margin, currency, purity_id=purity_id, conv_metal_code=conv_metal_code)
