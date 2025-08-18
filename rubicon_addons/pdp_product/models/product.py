from odoo import models, fields

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

