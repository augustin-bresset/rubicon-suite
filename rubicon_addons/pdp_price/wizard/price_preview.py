# wizard/price_preview.py
from odoo import models, fields, api

class PricePreview(models.TransientModel):
    _name = 'pdp.price.preview'
    _description = 'Price Preview'

    product_id = fields.Many2one('pdp.product', required=True, string='Product')
    margin_id = fields.Many2one('pdp.margin', string='Margin')
    date = fields.Date(default=fields.Date.context_today, required=True)
    currency_id = fields.Many2one('res.currency', required=True,
                                  default=lambda self: self.env.company.currency_id)

    line_ids = fields.One2many('pdp.price.preview.line', 'preview_id', string='Components')
    cost = fields.Monetary(currency_field='currency_id', compute='_compute_totals', store=False)
    margin = fields.Monetary(currency_field='currency_id', compute='_compute_totals', store=False)
    price = fields.Monetary(currency_field='currency_id', compute='_compute_totals', store=False)

    @api.depends('line_ids.cost', 'line_ids.margin')
    def _compute_totals(self):
        for rec in self:
            rec.cost = rec.currency_id.round(sum(rec.line_ids.mapped('cost')))
            rec.margin = rec.currency_id.round(sum(rec.line_ids.mapped('margin')))
            rec.price = rec.cost + rec.margin

    def action_compute(self):
        self.ensure_one()
        # Efface les lignes
        self.line_ids.unlink()

        components = [
            ('pdp.price.stone', 'stone'),
            ('pdp.price.metal', 'metal'),
            ('pdp.price.labor', 'labor'),
            ('pdp.price.addon', 'addon'),
            ('pdp.price.part', 'part'),
        ]
        vals_list = []
        for model, code in components:
            comp = self.env[model]
            payload = comp.compute(
                product=self.product_id,
                margin=self.margin_id,
                currency=self.currency_id,
                date=self.date,
            )
            warnings = payload.get('warnings', [])
            vals_list.append({
                'preview_id': self.id,
                'type': code,
                'cost': payload['cost'],
                'margin': payload['margin'],
                'price': payload['price'],
                'warnings': '\n'.join(warnings) if warnings else False,
            })
        self.env['pdp.price.preview.line'].create(vals_list)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pdp.price.preview',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_save(self):
        self.ensure_one()
        # Create pdp.price.product
        
        detail = []
        for line in self.line_ids:
            detail.append({
                'type': line.type,
                'cost': line.cost,
                'margin': line.margin,
                'price': line.price,
                'warnings': line.warnings or ''
            })
            
        vals = {
            'product_id': self.product_id.id,
            'margin_id': self.margin_id.id,
            'date': self.date,
            'currency_id': self.currency_id.id,
            'cost': self.cost,
            'margin': self.margin,
            'price': self.price,
            'detail_json': detail,
        }
        
        saved_record = self.env['pdp.price.product'].create(vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pdp.price.product',
            'res_id': saved_record.id,
            'view_mode': 'form',
            'target': 'current',
        }

class PricePreviewLine(models.TransientModel):
    _name = 'pdp.price.preview.line'
    _description = 'Price Preview Line'

    preview_id = fields.Many2one('pdp.price.preview', required=True, ondelete='cascade')
    type = fields.Selection([
        ('stone', 'Stones'),
        ('metal', 'Metals'),
        ('labor', 'Labor'),
        ('addon', 'Addons'),
        ('part', 'Parts'),
    ], required=True)
    cost = fields.Monetary(currency_field='currency_id')
    margin = fields.Monetary(currency_field='currency_id')
    price = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one(related='preview_id.currency_id', store=False, readonly=True)
    warnings = fields.Text(string='Warnings', readonly=True)
