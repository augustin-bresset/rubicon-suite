from odoo import models, fields

class PriceLine(models.Model):
    _name = 'pdp.price.line'

    price_id = fields.Many2one('pdp.price', required=True)
    component = fields.Selection([
        ('metal', 'Metal'),
        ('stone', 'Stone'),
        ('parts', 'Parts'),
        ('misc', 'Misc'),
        ('misc2', 'Misc2'),
        ('labor', 'Labor'),
        ('price', 'Price'),
        ('price2', 'Price2'),
        ('m_price', 'mPrice'),
        ('m_metal', 'mMetal'),
        ('m_stone', 'mStone'),
        ('m_labor', 'mLabor'),
        ('m_parts', 'mParts'),   
    ])
    
    metric = fields.Selection([
        ('cost', 'Cost'),
        ('price', 'Price'),
        ('margin', 'Margin'),
    ])
    
    value = fields.Float()
    
    