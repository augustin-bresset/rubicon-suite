
from odoo import fields, models

class MarginStoneConditional(models.Model):
    _name="pdp.margin.stone.conditional"
    _description="Stone Margin"
    
    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True,
    )
    
    stone_cat_id = fields.Many2one(
        string="Stone Category Code",
        comodel_name="pdp.stone.category",
        required=True,
        index=True
    )
    
    operator = fields.Selection([
        ('<' ,"is less than"),
        ('<=','is less than or equal to'),
        ('=' ,'is equal to'),
        ('>' ,'is more than'),
        ('>=','is more than or equal to')
    ])
    
    comparative_cost = fields.Monetary(
        string='Cost',
        currency_field="currency_id",
        required=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True
    )
    
    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )

    @staticmethod
    def use_operator(a, b, operator):
        if operator == '<':
            return a < b
        elif operator == '<=':
            return a <= b
        elif operator == '>':
            return a > b
        elif operator == '>=':
            return a >= b
        elif operator == '=':
            return a == b
        return None