from odoo import api, fields, models


class ProductFrontend(models.Model):
    _inherit = 'pdp.product'

    frontend_margin_id = fields.Many2one(
        'pdp.margin',
        string='Margin',
        default=lambda self: self._pdp_frontend_default_margin(),
    )
    frontend_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    frontend_purity_id = fields.Many2one(
        'pdp.metal.purity',
        string='Purity',
    )
    frontend_metal_conversion = fields.Selection(
        [
            ('standard', 'Standard'),
            ('gram_to_baht', 'Gram to Baht'),
            ('gram_to_ounce', 'Gram to Ounce'),
        ],
        string='Metal Conv.',
        default='standard',
    )
    frontend_usd_rate = fields.Float(string='US$ Rate', compute='_compute_frontend_usd_rate', store=False)
    frontend_date = fields.Date(default=fields.Date.context_today, string='Pricing Date')

    frontend_variant_ids = fields.Many2many(
        'pdp.product',
        compute='_compute_frontend_variants',
        string='Variants for Model',
        store=False,
    )
    frontend_variant_count = fields.Integer(
        compute='_compute_frontend_variants',
        string='Products Found',
        store=False,
    )

    model_picture_image = fields.Image(related='model_id.picture_image', readonly=True, store=False)

    frontend_stone_cost = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_stone_margin = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_stone_price = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)

    frontend_metal_cost = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_metal_margin = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_metal_price = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)

    frontend_labor_cost = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_labor_margin = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_labor_price = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)

    frontend_misc_cost = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_misc_margin = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_misc_price = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)

    frontend_parts_cost = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_parts_margin = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_parts_price = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)

    frontend_total_cost = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_total_margin = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)
    frontend_total_price = fields.Monetary(currency_field='frontend_currency_id', compute='_compute_frontend_costs', store=False)

    def _pdp_frontend_default_margin(self):
        return self.env['pdp.margin'].search([], limit=1)

    @api.depends('model_id')
    def _compute_frontend_variants(self):
        for product in self:
            if product.model_id:
                variants = self.search([('model_id', '=', product.model_id.id)])
            else:
                variants = self.browse()
            product.frontend_variant_ids = variants
            product.frontend_variant_count = len(variants)

    @api.depends('frontend_currency_id', 'frontend_date')
    def _compute_frontend_usd_rate(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        for product in self:
            currency = product.frontend_currency_id or self.env.company.currency_id
            if usd_currency and currency:
                product.frontend_usd_rate = usd_currency._convert(
                    1.0, currency, self.env.company, product.frontend_date or fields.Date.context_today(product)
                )
            else:
                product.frontend_usd_rate = 1.0

    @api.depends(
        'frontend_margin_id',
        'frontend_currency_id',
        'frontend_date',
        'frontend_purity_id',
        'frontend_metal_conversion',
        'code',
        'model_id',
        'stone_composition_id',
        'metal',
    )
    def _compute_frontend_costs(self):
        component_map = {
            'stone': 'pdp.price.stone',
            'metal': 'pdp.price.metal',
            'labor': 'pdp.price.labor',
            'addon': 'pdp.price.addon',
            'part': 'pdp.price.part',
        }
        for product in self:
            currency = product.frontend_currency_id or self.env.company.currency_id
            margin = product.frontend_margin_id or product._pdp_frontend_default_margin()
            date = product.frontend_date or fields.Date.context_today(product)
            results = {key: {'cost': 0.0, 'margin': 0.0, 'price': 0.0} for key in component_map}
            for key, model_name in component_map.items():
                try:
                    payload = self.env[model_name].compute(
                        product=product,
                        margin=margin,
                        currency=currency,
                        date=date,
                    )
                except Exception:
                    payload = {'cost': 0.0, 'margin': 0.0, 'price': 0.0}
                results[key] = payload

            product.frontend_stone_cost = results['stone']['cost']
            product.frontend_stone_margin = results['stone']['margin']
            product.frontend_stone_price = results['stone']['price']

            product.frontend_metal_cost = results['metal']['cost']
            product.frontend_metal_margin = results['metal']['margin']
            product.frontend_metal_price = results['metal']['price']

            product.frontend_labor_cost = results['labor']['cost']
            product.frontend_labor_margin = results['labor']['margin']
            product.frontend_labor_price = results['labor']['price']

            product.frontend_misc_cost = results['addon']['cost']
            product.frontend_misc_margin = results['addon']['margin']
            product.frontend_misc_price = results['addon']['price']

            product.frontend_parts_cost = results['part']['cost']
            product.frontend_parts_margin = results['part']['margin']
            product.frontend_parts_price = results['part']['price']

            total_cost = sum(value['cost'] for value in results.values())
            total_margin = sum(value['margin'] for value in results.values())
            product.frontend_total_cost = currency.round(total_cost) if currency else total_cost
            product.frontend_total_margin = currency.round(total_margin) if currency else total_margin
            product.frontend_total_price = product.frontend_total_cost + product.frontend_total_margin

    def action_frontend_preview_reset(self):
        """Placeholder for preview buttons."""
        return False