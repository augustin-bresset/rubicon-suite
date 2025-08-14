from odoo import models, fields, api

class ProductModel(models.Model):
    _name = 'pdp.product.model'
    _description = 'Product Model'

    _rec_name = "code"
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    code = fields.Char(string='Model Code', required=True, size=10)
    drawing = fields.Char(string='Drawing Reference', size=20)
    quotation = fields.Char(string='Quotation Reference', size=20)

    category = fields.Many2one(
        comodel_name='pdp.product.category',
        string='Model Category',
    )
    
    metal_weights_ids = fields.One2many(
        comodel_name='pdp.product.model.metal', 
        inverse_name='model', 
        string='Metal Weights')

    # Sibling models : OXXXA, OXXXB, OXXXC, ...
    parent_model = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Parent Model',
        help="If this model is a variation of another base model, link it here."
    )

    sibling_model_ids = fields.Many2many(
        comodel_name='pdp.product.model',
        compute='_compute_sibling_model_ids',
        string='Sibling Models',
        store=False,
    )
    
    # Set of models    
    matching_models = fields.Many2many(
        comodel_name='pdp.product.model',
        compute='_compute_related_matching_models',
        string='Matching Models',
        store=False,
    )

    def _compute_related_matching_models(self):
        for record in self:
            matchings = self.env['pdp.product.model.matching'].search([
                '|',
                ('model_one', '=', record.id),
                ('model_two', '=', record.id)
            ])
            related_models = set()
            for m in matchings:
                if m.model_one.id != record.id:
                    related_models.add(m.model_one.id)
                if m.model_two.id != record.id:
                    related_models.add(m.model_two.id)
            record.matching_models = list(related_models)
    
    def _compute_sibling_model_ids(self):
        for record in self:
            if record.parent_model:
                base_model = record.parent_model  
            else:
                base_model = record
            siblings = self.search([
            '|',
            ('parent_model', '=', base_model.id),
            ('id', '=', base_model.id),
        ])
        record.sibling_model_ids = siblings