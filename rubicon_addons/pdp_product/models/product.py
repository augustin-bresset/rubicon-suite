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
    
    stone_line_ids  = fields.One2many(
        related='stone_composition_id.stone_line_ids',
        string='Stones',
        readonly=False
    )
    
    total_stone_weight = fields.Float(
        string="Total Stone Weight",
        compute="_compute_total_stone_weight",
        store=True,
        digits=(7, 4)
    )

    @api.depends('stone_line_ids.weight', 'stone_line_ids.pieces')
    def _compute_total_stone_weight(self):
        for product in self:
            total = 0.0
            for line in product.stone_line_ids:
                total += (line.weight or 0.0) * (line.pieces or 1)
            product.total_stone_weight = total

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

    @api.model
    def copy_product_from_ui(self, source_id, new_code, options):
        """
        Duplicate a product with selected partial fields.
        Options dictionary allows granular control over what gets copied.
        """
        source = self.browse(source_id)
        if not source.exists():
            raise ValueError(f"Source product {source_id} not found.")

        # 1. Create the new blank product
        new_product = self.create({
            'code': new_code,
            'model_id': source.model_id.id if source.model_id else False,
            'active': True,
        })

        # 2. Copy stones
        if options.get('copy_stone') and source.stone_composition_id:
            old_comp = source.stone_composition_id
            stones = self.env['pdp.product.stone'].search([('composition_id', '=', old_comp.id)])
            if stones:
                new_comp = self.env['pdp.product.stone.composition'].create({'code': new_code})
                for s in stones:
                    self.env['pdp.product.stone'].create({
                        'composition_id': new_comp.id,
                        'stone_id': s.stone_id.id if s.stone_id else False,
                        'pieces': s.pieces,
                        'weight': s.weight,
                        'reshaped_shape_id': s.reshaped_shape_id.id if s.reshaped_shape_id else False,
                        'reshaped_size_id': s.reshaped_size_id.id if s.reshaped_size_id else False,
                        'reshaped_weight': s.reshaped_weight,
                    })
                new_product.write({'stone_composition_id': new_comp.id})

        # 3. Copy labor product costs
        if options.get('copy_labor'):
            labors = self.env['pdp.labor.cost.product'].search([('product_id', '=', source.id)])
            for l in labors:
                self.env['pdp.labor.cost.product'].create({
                    'product_id': new_product.id,
                    'labor_id': l.labor_id.id if l.labor_id else False,
                    'cost': l.cost,
                    'currency_id': l.currency_id.id if l.currency_id else False,
                })

        # 4. Copy parts
        if options.get('copy_parts'):
            parts = self.env['pdp.product.part'].search([('product_id', '=', source.id)])
            for p in parts:
                self.env['pdp.product.part'].create({
                    'product_id': new_product.id,
                    'part_id': p.part_id.id if p.part_id else False,
                    'quantity': p.quantity,
                })

        # 5. Copy misc (addon costs)
        if options.get('copy_misc'):
            addons = self.env['pdp.addon.cost'].search([('product_id', '=', source.id)])
            for a in addons:
                self.env['pdp.addon.cost'].create({
                    'product_id': new_product.id,
                    'addon_id': a.addon_id.id if a.addon_id else False,
                    'cost': a.cost,
                    'currency_id': a.currency_id.id if a.currency_id else False,
                })

        return new_product.id
