# pdp_price/wizard/price_preview.py
from odoo import api, fields, models


class PricePreviewWizard(models.TransientModel):
    _name = "pdp.price.preview.wizard"
    _description = "Price Preview"
    _order = "id desc"

    # --------------------
    # Champs du wizard
    # --------------------
    product_id = fields.Many2one(
        'pdp.product',
        string='Product',
        required=True,
    )
    margin_id = fields.Many2one(
        'pdp.margin',
        string='Margin',
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True,
    )

    line_ids = fields.One2many(
        'pdp.price.preview.line',
        'wizard_id',
        string='Lines',
        readonly=True,
        copy=False,
    )

    # --------------------
    # Onchange = pas d'INSERT ! -> O2M commands
    # --------------------
    @api.onchange('product_id', 'margin_id', 'date', 'currency_id')
    def _onchange_recompute(self):
        for wiz in self:
            if wiz.product_id and wiz.currency_id and wiz.date:
                cmds = wiz._build_line_commands()
                # En onchange on assigne directement -> pas de write()
                wiz.line_ids = cmds

    # --------------------
    # Bouton (persisté) = write()
    # --------------------
    def action_recompute(self):
        self.ensure_one()
        cmds = self._build_line_commands()
        # Ici le wizard est persisté -> OK pour write()
        self.write({'line_ids': cmds})
        return self._action_open_self()

    # --------------------
    # Construit les O2M commands à partir du moteur
    # --------------------
    def _build_line_commands(self):
        """Retourne [(5,0,0), (0,0,vals), ...]"""
        self.ensure_one()

        engine = self.env['pdp.price.engine']
        data = engine.compute_price_sheet(
            product=self.product_id,
            margin=self.margin_id,
            date=self.date,
            currency=self.currency_id,
        )

        cmds = [(5, 0, 0)]  # purge
        seq = 1
        for r in (data.get('rows') or []):
            cmds.append((0, 0, {
                'sequence': seq,
                'component': r['component'],
                'label': r['label'],
                'cost': r['cost'],
                'margin': r['margin'],
                'price': r['price'],
            }))
            seq += 1

        total = data.get('total') or {'cost': 0.0, 'margin': 0.0, 'price': 0.0}
        cmds.append((0, 0, {
            'sequence': 9999,
            'component': 'total',
            'label': 'TOTAL',
            'cost': total['cost'],
            'margin': total['margin'],
            'price': total['price'],
        }))
        return cmds

    # --------------------
    # Action d'ouverture (modal)
    # --------------------
    def _action_open_self(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Price Preview',
            'res_model': 'pdp.price.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            # Ceinture & bretelles si quelqu’un ouvre les lines ailleurs :
            'context': {'default_wizard_id': self.id},
        }


class PricePreviewLine(models.TransientModel):
    _name = "pdp.price.preview.line"
    _description = "Price Preview Line"
    _order = "sequence, id"

    # --------------------
    # Liens & ordre
    # --------------------
    wizard_id = fields.Many2one(
        'pdp.price.preview.wizard',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.context.get('default_wizard_id'),
    )
    sequence = fields.Integer(default=10)

    # --------------------
    # Données de ligne
    # --------------------
    component = fields.Selection([
        ('metal', 'Metal'),
        ('stone', 'Stone'),
        ('labor', 'Labor'),
        ('parts', 'Parts'),
        ('addon', 'Addon'),
        ('misc', 'Misc'),
        ('total', 'Total'),
    ], required=True)

    label = fields.Char(required=True)

    # Montants en devise du wizard (readonly côté UI)
    cost = fields.Monetary(currency_field='currency_id', readonly=True)
    margin = fields.Monetary(currency_field='currency_id', readonly=True)
    price = fields.Monetary(currency_field='currency_id', readonly=True)

    # Devise liée au wizard (pas stocké)
    currency_id = fields.Many2one(
        'res.currency',
        related='wizard_id.currency_id',
        store=False,
        readonly=True,
    )

    # --------------------
    # Garde-fou : interdire un create() sans wizard_id
    # (au cas où quelqu’un ferait un create() direct)
    # --------------------
    @api.model
    def create(self, vals):
        vals = dict(vals or {})
        if not vals.get('wizard_id'):
            ctx_wiz = self.env.context.get('default_wizard_id')
            if ctx_wiz:
                vals['wizard_id'] = ctx_wiz
        if not vals.get('wizard_id'):
            # Empêche tout INSERT NULL sur wizard_id
            raise ValueError("wizard_id is required for pdp.price.preview.line")
        return super().create(vals)
