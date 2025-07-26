from odoo import models, fields

class Product(models.Model):
    _name = 'pdp.product'
    _description = 'Product is defined by his model and a specific composition of stones'

    _rec_name='code'
    
    code = fields.Char(
        string='Design reference code', 
        required=True, 
        size=100)
    
    category_code = fields.Many2one(
        comodel_name='pdp.product.category',
        string='Category',
    )
    
    model_code = fields.Many2one(
        comodel_name='pdp.product.model',
        string='Model',
    )
    
    product_stone_code = fields.Char(
        string='Produc Stones Code',
    )
    
    stone_composition = fields.Char(
        string='Stone Composition',
        size=40
    )
    
    metal_code = fields.Char(
        string='Metal code', 
        size=10
    )
    
    
    active          = fields.Boolean(string="Is active")
    create_date     = fields.Datetime(string="Date of Creation")
    in_collection   = fields.Boolean(string="Is in a collection")
    remark          = fields.Char(string="Remark", size=100)    
    
    parts        = fields.One2many(
        comodel_name='pdp.product.part',
        inverse_name='product_code'
    )

