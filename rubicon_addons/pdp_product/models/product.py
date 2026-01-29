from odoo import models, fields, api

class Product(models.Model):
    _name = 'pdp.product'
    _description = 'Product is defined by his model and a specific composition of stones'

    _rec_name='code'
    
    code = fields.Char(
        string='Design reference code', 
        required=True, 
        index=True
    )
    
    category_id = fields.Many2one(
        comodel_name='pdp.product.category',
        string='Category',
        index=True
    )
    
    model_id = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Model',
        index=True
    )
    
    stone_composition_id = fields.Many2one(
        comodel_name='pdp.product.stone.composition',
        string='Stone Composition',
        index=True
    )
    
    metal = fields.Char(
        string='Metal code'
    )
    
    
    active          = fields.Boolean(string="Is active")
    create_date     = fields.Datetime(string="Date of Creation")
    in_collection   = fields.Boolean(string="Is in a collection")
    remark          = fields.Text(string="Remark")    
    
    part_ids        = fields.One2many(
        comodel_name='pdp.product.part',
        inverse_name='product_id'
    )

    # =========================================================================
    # Domain Methods - Reusable by API, Cron, OWL, Reports
    # =========================================================================

    def to_dict(self):
        """Return product data as JSON-serializable dict."""
        self.ensure_one()
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name if hasattr(self, 'name') else self.code,
            'model_id': self.model_id.id if self.model_id else None,
            'model_code': self.model_id.code if self.model_id else '',
            'category_id': self.category_id.id if self.category_id else None,
            'create_date': str(self.create_date) if self.create_date else None,
            'active': self.active,
        }

    def get_full_data(self, margin_id=None, currency_id=None):
        """
        Return complete product data including weights and pricing.
        Main entry point for API, Cron, OWL, Reports.
        """
        self.ensure_one()
        return {
            'product': self.to_dict(),
            'weights': self.get_weight_data(),
            'costing': self.get_costing_data(margin_id, currency_id),
            'metadata': self.get_metadata(),
        }

    def get_weight_data(self):
        """Return weight breakdown: stones (original/recut) and metals."""
        self.ensure_one()
        stone_original = []
        stone_recut = []
        metal = []

        # Stones from composition
        if self.stone_composition_id:
            for line in self.stone_composition_id.stone_line_ids:
                stone_original.append(line.to_dict_original())
                stone_recut.append(line.to_dict_recut())

        # Metals from model
        if self.model_id:
            metal = self.model_id.get_metal_weights()

        return {
            'stone_original': stone_original,
            'stone_recut': stone_recut,
            'metal': metal,
        }

    def get_costing_data(self, margin_id=None, currency_id=None):
        """Compute pricing using price service."""
        self.ensure_one()
        PriceService = self.env.get('pdp.price.service')
        if PriceService:
            margin = self.env['pdp.margin'].browse(int(margin_id)) if margin_id else None
            currency = self.env['res.currency'].browse(int(currency_id)) if currency_id else self.env.company.currency_id
            return PriceService.compute_product_price(self, margin, currency)
        return {'lines': [], 'totals': {'cost': 0, 'margin': 0, 'price': 0}}

    def get_metadata(self):
        """Return reference data for dropdowns."""
        return {
            'all_currencies': self.env['res.currency'].search_read(
                [('active', '=', True)], ['id', 'name', 'symbol']
            ),
            'all_margins': self.env['pdp.margin'].search_read([], ['id', 'name', 'code']),
        }
