# pdp_price/services/price_engine.py
from odoo import api, models, fields

class PriceEngine(models.AbstractModel):
    _name = "pdp.price.engine"
    _description = "Price computation engine (no UI)"

    @api.model
    def compute_price_sheet(self, *, product, margin, date, currency):
        """Retourne un dict:
        {
          'rows': [ {'component','label','cost','margin','price'}, ... ],
          'total': {'cost','margin','price'},
        }
        """
        rows = []
        rows += self._rows_addons(product=product, margin=margin, date=date, currency=currency)
        # TODO: rows += self._rows_metals(...)
        # TODO: rows += self._rows_stones(...)
        # TODO: rows += self._rows_labor(...)
        # TODO: rows += self._rows_parts(...)

        tot_cost   = sum(r['cost']   for r in rows)
        tot_margin = sum(r['margin'] for r in rows)
        tot_price  = tot_cost + tot_margin
        total = {
            'cost':   currency.round(tot_cost),
            'margin': currency.round(tot_margin),
            'price':  currency.round(tot_price),
        }
        return {'rows': rows, 'total': total}

    # ---------- Addons ----------
    def _rows_addons(self, *, product, margin, date, currency):
        """ Agrège pdp.addon.cost par (addon_code, currency) puis convertit.
            Applique la marge par type d’addon via pdp.margin.addon (margin_code+addon_code).
        """
        Currency   = self.env['res.currency']
        AddonCost  = self.env['pdp.addon.cost']     # champs attendus: product_code, addon_code, currency, cost
        MarginLine = self.env['pdp.margin.addon']   # champs: margin_code, addon_code, rate

        rows = []
        if not product:
            return rows

        # read_group: 1 ligne par (addon_code, currency)
        groups = AddonCost.read_group(
            domain=[('product_code', '=', product.id)],
            fields=['cost:sum', 'currency', 'addon_code'],
            groupby=['addon_code', 'currency'],
        )

        # précharger les taux par addon
        rate_by_addon = {}
        if margin:
            for r in MarginLine.search([('margin_code', '=', margin.id)]):
                rate_by_addon[r.addon_code.id] = r.rate or 0.0

        # cumuler par addon → montant converti dans la devise cible
        totals_by_addon = {}  # addon_id -> cost_in_target_currency
        for g in groups:
            amount = g.get('cost_sum') or 0.0
            cur_id = (g.get('currency') or [currency.id])[0]
            addon_id = (g.get('addon_code') or [False])[0]
            cur = Currency.browse(cur_id)
            amount_conv = cur._convert(amount, currency, company=self.env.company, date=date)
            totals_by_addon[addon_id] = totals_by_addon.get(addon_id, 0.0) + amount_conv

        # lignes finales
        for addon_id, cost in totals_by_addon.items():
            rate = rate_by_addon.get(addon_id, 0.0) if margin else 0.0
            line_margin = cost * rate
            label = self.env['pdp.addon.type'].browse(addon_id).display_name if addon_id else "Addon"
            rows.append({
                'component': 'addon',
                'label': label,
                'cost':   currency.round(cost),
                'margin': currency.round(line_margin),
                'price':  currency.round(cost + line_margin),
            })
        return rows
