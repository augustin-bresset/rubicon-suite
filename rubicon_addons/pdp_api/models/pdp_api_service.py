from odoo import models, fields, api


class PdpApiService(models.AbstractModel):
    """
    PDP API Service - Thin wrapper calling domain methods.
    
    Business logic is now in domain models:
    - pdp.product: to_dict(), get_full_data(), get_weight_data()
    - pdp.product.stone: to_dict_original(), to_dict_recut()
    - pdp.product.model: get_metal_weights()
    - pdp.price.service: compute_product_price()
    """
    _name = 'pdp.api.service'
    _description = 'PDP API Service'

    # =========================================================================
    # PUBLIC API METHODS - Thin wrappers for HTTP controllers
    # =========================================================================

    @api.model
    def get_full_pdp(self, product_id, margin_id=None, currency_id=None):
        """
        Main entry point to get all data for a PDP page.
        Delegates to domain method pdp.product.get_full_data().
        """
        product = self.env['pdp.product'].browse(product_id)
        if not product.exists():
            return {'error': 'Product not found'}
        return product.get_full_data(margin_id, currency_id)

    @api.model
    def get_pdp_state(self, product_id=None, model_id=None):
        """
        Returns the full state required to render the PDP Frontend.
        Used by QWeb templates.
        """
        Product = self.env['pdp.product']
        Model = self.env['pdp.product.model']

        # 1. Resolve Product/Model
        product = Product.browse(int(product_id)) if product_id else Product.browse()
        if not product.exists() and model_id:
            product = Product.search([('model_id', '=', int(model_id))], limit=1)

        current_model_id = product.model_id.id if product else (int(model_id) if model_id else None)

        # 2. Fetch Lists (Context Data)
        all_models = Model.search([])
        model_products = Product.search([('model_id', '=', current_model_id)]) if current_model_id else []
        margins = self.env['pdp.margin'].search([])
        currencies = self.env['res.currency'].search([('active', '=', True)])
        metals = self.env['pdp.metal'].search([])

        # 3. Compute Pricing using price service
        price_preview = None
        if product.exists():
            try:
                Margin = self.env['pdp.margin']
                margin = Margin.search([], limit=1)
                currency = self.env.company.currency_id

                price_preview = self.env['pdp.price.preview'].create({
                    'product_id': product.id,
                    'margin_id': margin.id if margin else False,
                    'currency_id': currency.id,
                    'date': fields.Date.context_today(self),
                })
                price_preview.action_compute()
            except Exception:
                pass

        # 4. Compute Weight Summary using domain method
        weight_summary = {'total_stone_weight': 0, 'total_stone_pieces': 0, 'total_metal_weight': 0}
        if product.exists():
            if product.stone_composition_id:
                ws = product.stone_composition_id.get_weight_summary()
                weight_summary['total_stone_weight'] = ws['total_weight']
                weight_summary['total_stone_pieces'] = ws['total_pieces']
            if product.model_id:
                weight_summary['total_metal_weight'] = product.model_id.get_total_metal_weight()

        # 5. Assemble State
        return {
            'product': product,
            'current_model_id': current_model_id,
            'all_models': all_models,
            'model_products': model_products,
            'margins': margins,
            'currencies': currencies,
            'metals': metals,
            'price_preview': price_preview,
            'total_stone_weight': weight_summary['total_stone_weight'],
            'total_stone_pieces': weight_summary['total_stone_pieces'],
            'total_metal_weight': weight_summary['total_metal_weight'],
        }

    @api.model
    def compute_price(self, product_id, margin_id, currency_id, metal_id=None, purity_id=None):
        """
        JSON Endpoint to recalculate prices.
        Delegates to pdp.price.service.compute_product_price().
        """
        product = self.env['pdp.product'].browse(int(product_id))
        if not product.exists():
            return {'error': 'Product not found'}

        margin = self.env['pdp.margin'].browse(int(margin_id)) if margin_id else None
        currency = self.env['res.currency'].browse(int(currency_id))

        PriceService = self.env['pdp.price.service']
        return PriceService.compute_product_price(product, margin, currency, purity_id=purity_id)
