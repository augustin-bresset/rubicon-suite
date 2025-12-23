from odoo import models, fields, api, _

class PdpFrontendService(models.AbstractModel):
    _name = 'pdp.frontend.service'
    _description = 'PDP Frontend Facade Service'

    @api.model
    def get_pdp_state(self, product_id=None, model_id=None):
        """
        Returns the full state required to render the PDP Frontend.
        Dumb-client ready structure.
        """
        Product = self.env['pdp.product']
        Model = self.env['pdp.product.model']
        
        # 1. Resolve Product/Model
        product = Product.browse(int(product_id)) if product_id else Product.browse()
        if not product.exists() and model_id:
            # Try to find a product for this model
            product = Product.search([('model_id', '=', int(model_id))], limit=1)

        current_model_id = product.model_id.id if product else (int(model_id) if model_id else None)
        
        # 2. Fetch Lists (Context Data)
        all_models = Model.search([])
        model_products = Product.search([('model_id', '=', current_model_id)]) if current_model_id else []
        margins = self.env['pdp.margin'].search([])
        currencies = self.env['res.currency'].search([('active', '=', True)])
        metals = self.env['pdp.metal'].search([])

        # 3. Compute Pricing (Dynamic)
        price_preview = None
        if product:
            try:
                # Default Logic for pricing context
                Margin = self.env['pdp.margin']
                margin = Margin.search([], limit=1)
                currency = self.env.company.currency_id
                
                # Create transient preview (Pricing Engine)
                price_preview = self.env['pdp.price.preview'].create({
                    'product_id': product.id,
                    'margin_id': margin.id if margin else False,
                    'currency_id': currency.id,
                    'date': fields.Date.context_today(self),
                })
                price_preview.action_compute()
            except Exception as e:
                # Log error but don't crash the whole page
                print(f"PDP Facade Pricing Error: {e}")

        # 4. Compute Weights (Static/Physical)
        weight_summary = self._compute_weight_summary(product)

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
    def _compute_weight_summary(self, product):
        """
        Centralized logic for weight calculation.
        """
        total_stone_weight = 0.0
        total_stone_pieces = 0
        total_metal_weight = 0.0

        if product:
            # Stones
            if product.stone_composition_id and product.stone_composition_id.stone_line_ids:
                for line in product.stone_composition_id.stone_line_ids:
                    total_stone_pieces += line.pieces
                    try:
                        # Cleaning dirty data (legacy behavior preservation)
                        w_val = float(line.weight.replace(',', '.')) if line.weight else 0.0
                        # Assumption: 'weight' is per piece
                        total_stone_weight += w_val * line.pieces 
                    except ValueError:
                        pass

            # Metals
            if product.model_id and product.model_id.metal_weights_ids:
                for m in product.model_id.metal_weights_ids:
                    total_metal_weight += m.weight

        return {
            'total_stone_weight': total_stone_weight,
            'total_stone_pieces': total_stone_pieces,
            'total_metal_weight': total_metal_weight,
        }
