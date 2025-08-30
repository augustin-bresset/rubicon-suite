from odoo import models, fields, api

class PriceLabor(models.TransientModel):
    _name = 'pdp.price.labor'
    _description = 'Labor Price Component'
    _inherit = "pdp.price.component"

    @api.model
    def compute(self, *, product, margin, currency, date):
        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        LaborCostModel = self.env['pdp.labor.cost.model'].with_context(clean_ctx)
        LaborCostProduct = self.env['pdp.labor.cost.product'].with_context(clean_ctx)
        LaborMargin = self.env['pdp.margin.labor'].with_context(clean_ctx)

        total_cost = total_margin = 0.0

        for labor in self.env['pdp.labor.type'].search([]):

            # Récupère éventuels coûts modèle et produit
            model_line = LaborCostModel.search([
                ('model_id', '=', product.model_id.id),
                ('labor_id', '=', labor.id)
            ], limit=1)

            product_line = LaborCostProduct.search([
                ('product_id', '=', product.id),
                ('labor_id', '=', labor.id)
            ], limit=1)

            if not model_line and not product_line:
                continue

            # Conversion devises
            model_cost = self._convert(model_line.cost, model_line.currency_id, currency, date) if model_line else 0.0
            product_cost = self._convert(product_line.cost, product_line.currency_id, currency, date) if product_line else 0.0

            # Règle de priorité :
            #  - si product_cost > 0 → on prend product_cost
            #  - sinon, si model_cost > 0 → fallback sur model_cost
            #  - sinon, product_cost (qui est 0.0)
            if product_cost > 0.0:
                cost = product_cost
            elif model_cost > 0.0:
                cost = model_cost
            else:
                cost = product_cost

            total_cost += cost

            # Application de la marge par type
            rate = 1.0
            if margin:
                mline = LaborMargin.search([
                    ('margin_id', '=', margin.id),
                    ('labor_id', '=', labor.id),
                ], limit=1)
                if mline:
                    rate = mline.rate or 1.0

            total_margin += (rate - 1.0) * cost

        return self._payload('labor', total_cost, total_margin, currency)
