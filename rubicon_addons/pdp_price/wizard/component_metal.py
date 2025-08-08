from odoo import models, fields, api

class PriceMetal(models.TransientModel):
    _name = 'pdp.price.metal'
    _description = 'Metal Price Component'
    _inherit='pdp.price.component'  


    @api.depends()
    def compute(self, *, product_code, margin_code=None, currency, date):
        """
        product.model_metal -> (weight, [model_code], metal_code 
        
        """
        cost = 0.0
        margin = 0.0
        
        product_metal = self.env['pdp.product.model.metal'].search([
                ('model_code', '=', product_code.model_code)
            ])
        
        metal = self.env['pdp.metal'].search([
            ('code', '=', product_metal.metal_code)
        ])
        
        ## NOT SURE IF THE REF IS GOOD
        usd_cost = metal.cost*0.001*product_metal.weight
        usd_curr = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        cost = self._convert(usd_cost, usd_curr, currency, date)

        margin = margin.rate or 1.0
        margin *= cost

        return self.compute_payload('addon', cost, margin, currency)
    