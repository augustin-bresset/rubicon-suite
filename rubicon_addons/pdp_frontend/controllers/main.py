from odoo import http, fields
from odoo.http import request


class PDPFrontendController(http.Controller):
    @http.route(["/pdp", "/pdp/<model('pdp.product'):product>"], type="http", auth="user")
    def pdp_home(self, product=None, **kwargs):
        """Serve the PDP frontend preview page using the unified API Service."""
        
        # Resolve IDs from args or kwargs
        product_id = product.id if product else kwargs.get('product_id')
        model_id = kwargs.get('model_id')

        # Call the unified API Service
        values = request.env['pdp.api.service'].get_pdp_state(product_id=product_id, model_id=model_id)

        return request.render("pdp_frontend.pdp_frontend_page", values)

    @http.route("/pdp/create", type="http", auth="user", methods=["POST"], csrf=False)
    def pdp_create(self, model_id, **kwargs):
        Product = request.env['pdp.product']
        if model_id:
            new_product = Product.create({
                'model_id': int(model_id),
                'code': 'NEW-DESIGN', 
                # Add default stone composition if needed, or leave empty
            })
            return request.redirect(f"/pdp?product_id={new_product.id}")
        return request.redirect("/pdp")

    @http.route("/pdp/copy/<int:product_id>", type="http", auth="user", methods=["POST"], csrf=False)
    def pdp_copy(self, product_id, **kwargs):
        Product = request.env['pdp.product']
        product = Product.browse(product_id)
        if product.exists():
            new_product = product.copy({'code': f"{product.code} (Copy)"})
            return request.redirect(f"/pdp?product_id={new_product.id}")
        return request.redirect("/pdp")

    @http.route("/pdp/delete/<int:product_id>", type="http", auth="user", methods=["POST"], csrf=False)
    def pdp_delete(self, product_id, **kwargs):
        Product = request.env['pdp.product']
        product = Product.browse(product_id)
        if product.exists():
            model_id = product.model_id.id
            product.unlink()
            return request.redirect(f"/pdp?model_id={model_id}")
        return request.redirect("/pdp")
    
    @http.route("/pdp/save", type="http", auth="user", methods=["POST"], csrf=False)
    def pdp_save(self, product_id=None, code=None, **kwargs):
        """Save product data from the frontend form."""
        try:
            if not product_id:
                return request.redirect("/pdp")
            
            Product = request.env['pdp.product']
            product = Product.browse(int(product_id))
            
            if product.exists():
                vals = {}
                if code:
                    vals['code'] = code
                # Add more fields as needed from kwargs
                if vals:
                    product.write(vals)
                return request.redirect(f"/pdp?product_id={product.id}")
            return request.redirect("/pdp")
        except Exception as e:
            # Log error and redirect
            return request.redirect(f"/pdp?error={str(e)}")

    @http.route("/pdp/create_copy", type="http", auth="user", methods=["POST"], csrf=False)
    def pdp_create_copy(self, source_product_id=None, new_code=None, **kwargs):
        """Create a new product by copying an existing one."""
        try:
            if not source_product_id:
                return request.redirect("/pdp")
            
            Product = request.env['pdp.product']
            source = Product.browse(int(source_product_id))
            
            if source.exists():
                copy_code = new_code if new_code else f"{source.code} (Copy)"
                new_product = source.copy({'code': copy_code})
                return request.redirect(f"/pdp?product_id={new_product.id}")
            return request.redirect("/pdp")
        except Exception as e:
            return request.redirect(f"/pdp?error={str(e)}")

    @http.route("/pdp/create_blank", type="http", auth="user", methods=["POST"], csrf=False)
    def pdp_create_blank(self, model_id=None, new_code=None, **kwargs):
        """Create a new blank product for a model."""
        try:
            if not model_id:
                return request.redirect("/pdp")
            
            Product = request.env['pdp.product']
            code = new_code if new_code else 'NEW-DESIGN'
            
            new_product = Product.create({
                'model_id': int(model_id),
                'code': code,
            })
            return request.redirect(f"/pdp?product_id={new_product.id}")
        except Exception as e:
            return request.redirect(f"/pdp?error={str(e)}")

    @http.route("/pdp/update_price", type="json", auth="user")
    def pdp_update_price(self, product_id, margin_id, currency_id, metal_id=None, price_source=None):
        """
        JSON Endpoint to recalculate prices based on frontend parameters.
        """
        try:
            Product = request.env['pdp.product']
            price_preview_model = request.env['pdp.price.preview']
            
            product = Product.browse(int(product_id))
            if not product.exists():
                return {'error': 'Product not found'}

            # Create ephemeral preview
            preview = price_preview_model.create({
                'product_id': product.id,
                'margin_id': int(margin_id) if margin_id else False,
                'currency_id': int(currency_id),
                'date': fields.Date.context_today(request.env.user),
            })
            preview.action_compute()

            # Return ready-to-render data or raw values
            # Using raw values for client-side rendering is cleaner for simple table updates
            lines = []
            for line in preview.line_ids:
                lines.append({
                    'type': line.type,
                    'cost': line.cost,
                    'margin': line.margin,
                    'price': line.price,
                })
            
            # Formats
            currency = request.env['res.currency'].browse(int(currency_id))

            return {
                'lines': lines,
                'totals': {
                    'cost': preview.cost,
                    'margin': preview.margin,
                    'price': preview.price,
                },
                'currency': {
                    'symbol': currency.symbol,
                    'position': currency.position,
                    'rate': currency.rate or 1.0, 
                }
            }
        except Exception as e:
            return {'error': str(e)}