from odoo import models, fields, api

class PriceStone(models.TransientModel):
    _name = 'pdp.price.stone'
    _description = 'Price Base Component'
    _inherit='pdp.price.component'  

    @api.depends()
    def compute(self, *, product_code, margin_code=None, currency, date):
        total_cost = 0.0
        total_margin = 0.0
        
        product_stones = self.env['pdp.product.stone'].search([
            ('code', '=', product_code.composition_code)
        ])
        
        for product_stone in product_stones:
            curr_id = product_stone.stone_code.currency_id
            stones_cost = self._convert(
                amount=product_stone.stone_code.cost,
                from_cur=curr_id,
                to_cur=currency,
                date=date)
            stones_cost *= product_stone.pieces
            if margin_code:
                margin_stone = self.env['pdp.margin.stone'].search([
                    ('margin_code', '=', margin_code.code)
                    ('stone_type_code', '=', product_stone.stone_code.type_code),
                ])
                
                stones_margin = (margin_stone-1.0)*stones_cost
            else:
                stones_margin = 0.0
            
            total_cost += stones_cost
            total_margin += stones_margin

        return self.compute_payload('stone', total_cost, total_margin, currency)        