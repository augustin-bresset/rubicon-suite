from odoo import http, fields
from odoo.http import request


class PDPFrontendController(http.Controller):
    @http.route(["/pdp", "/pdp/<model('pdp.product'):product>"], type="http", auth="user")
    def pdp_home(self, product=None, **kwargs):
        """Serve the PDP frontend preview page."""
        Product = request.env['pdp.product']
        Model = request.env['pdp.product.model']
        
        Product = request.env['pdp.product']
        Model = request.env['pdp.product.model']
        
        # Fetch all models for the dropdown
        all_models = Model.search([])
        
        # If no product is provided, try to find one
        if not product:
            model_id = kwargs.get('model_id')
            domain = [('model_id', '=', int(model_id))] if model_id else []
            product = Product.search(domain, limit=1)
            
        # Pricing Logic
        price_preview = None
        if product:
            try:
                # Default Margin and Currency
                Margin = request.env['pdp.margin']
                margin = Margin.search([], limit=1)
                currency = request.env.company.currency_id
                
                price_preview = request.env['pdp.price.preview'].create({
                    'product_id': product.id,
                    'margin_id': margin.id if margin else False,
                    'currency_id': currency.id,
                    'date': fields.Date.context_today(request.env.user),
                })
                price_preview.action_compute()
            except Exception as e:
                # Fallback if pricing fails (e.g. missing configuration)
                request.env.cr.rollback()
                print(f"Pricing Error: {e}")

        # Fetch all products for the current model (for the design selector)
        model_products = Product.search([('model_id', '=', product.model_id.id)]) if product else []

        values = {
            'product': product,
            'all_models': all_models,
            'model_products': model_products,
            'current_model_id': product.model_id.id if product else (int(kwargs.get('model_id')) if kwargs.get('model_id') else None),
            'price_preview': price_preview,
        }
        return request.render("pdp_frontend.pdp_frontend_page", values)