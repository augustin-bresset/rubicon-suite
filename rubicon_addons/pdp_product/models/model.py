from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductModel(models.Model):
    _name = 'pdp.product.model'
    _description = 'Product Model'

    _rec_name = "code"
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    code = fields.Char(string='Model Code', required=True, index=True)

    drawing = fields.Char(string='Drawing Reference')
    quotation = fields.Char(string='Quotation Reference')
    
    category_id = fields.Many2one(
        comodel_name='pdp.product.category',
        string='Model Category',
        index=True,
    )
    
    metal_weights_ids = fields.One2many(
        comodel_name='pdp.product.model.metal', 
        inverse_name='model_id', 
        string='Metal Weights',
        )

    # Sibling models : OXXXA, OXXXB, OXXXC, ...
    parent_model_id = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Parent Model',
        help="If this model is a variation of another base model, link it here.",
        index=True
    )

    sibling_model_ids = fields.Many2many(
        comodel_name='pdp.product.model',
        compute='_compute_sibling_model_ids',
        string='Sibling Models',
        store=False,
    )
    
    # Set of models    
    matching_model_ids = fields.Many2many(
        comodel_name='pdp.product.model',
        compute='_compute_related_matching_models',
        string='Matching Models',
        store=False,
    )
    
    def _compute_related_matching_models(self):
        for record in self:
            matchings = self.env['pdp.product.model.matching'].search([
                '|',
                ('model_one_id', '=', record.id),
                ('model_two_id', '=', record.id)
            ])
            related_models = set()
            for m in matchings:
                if m.model_one_id.id != record.id:
                    related_models.add(m.model_one_id.id)
                if m.model_two_id.id != record.id:
                    related_models.add(m.model_two_id.id)
            record.matching_model_ids = list(related_models)
    
    def _compute_sibling_model_ids(self):
        for record in self:
            if record.parent_model_id:
                base_model = record.parent_model_id  
            else:
                base_model = record
            siblings = self.search([
            '|',
            ('parent_model_id', '=', base_model.id),
            ('id', '=', base_model.id),
        ])
        record.sibling_model_ids = siblings
        
    # =========================================================================
    # Domain Methods - Reusable by API, Cron, OWL, Reports
    # =========================================================================

    @api.ondelete(at_uninstall=False)
    def _unlink_except_models_with_products(self):
        """Deleting a model leaves its products orphaned (model_id set null).

        The web client's generic "delete records?" dialog does not say that,
        so refuse until the products are gone. Migration tooling that wipes
        on purpose (rubicon_demo, cleanup scripts) passes the
        `rubicon_force_delete` context key.
        """
        if self.env.context.get('rubicon_force_delete'):
            return
        Product = self.env['pdp.product'].with_context(active_test=False)
        for model in self:
            count = Product.search_count([('model_id', '=', model.id)])
            if count:
                raise UserError(self.env._(
                    "Model %(code)s still has %(count)s product(s). Delete or move "
                    "them first: deleting the model would leave them without a model.",
                    code=model.code, count=count))

    def to_dict(self):
        """Return model data as JSON-serializable dict."""
        self.ensure_one()
        return {
            'id': self.id,
            'code': self.code,
            'drawing': self.drawing,
            'quotation': self.quotation,
            'category_id': self.category_id.id if self.category_id else None,
        }

    def get_metal_weights(self):
        """Return list of metal weight dicts."""
        self.ensure_one()
        return [m.to_dict() for m in self.metal_weights_ids]

    def get_total_metal_weight(self):
        """Return sum of all metal weights in grams."""
        self.ensure_one()
        return sum(m.weight for m in self.metal_weights_ids)

