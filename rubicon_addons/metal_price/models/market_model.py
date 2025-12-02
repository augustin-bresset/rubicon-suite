+58-0
# rubicon_addons/pdp_metal_market/models/market_models.py
import csv
import io
from datetime import date

from odoo import models, fields, api

class MarketMetal(models.Model):
    _name = "pdp.market.metal"
    _description = "Base commodity metal"
    _order = "code"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    base_unit = fields.Selection([('troy_oz', 'Troy ounce'), ('gram', 'Gram')], default='troy_oz', required=True)
    base_currency_id = fields.Many2one('res.currency', required=True, default=lambda s: s.env.ref('base.USD'))

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Metal code must be unique.')
    ]


class MarketPrice(models.Model):
    _name = "pdp.market.price"
    _description = "Daily spot price per metal"
    _order = "date desc"

    metal_id = fields.Many2one('pdp.market.metal', required=True, index=True, ondelete='cascade')
    date = fields.Date(required=True, index=True)
    price = fields.Monetary(currency_field='currency_id', required=True)
    currency_id = fields.Many2one(related='metal_id.base_currency_id', store=True, readonly=True)
    source_id = fields.Many2one('pdp.market.source')

    _sql_constraints = [
        ('uniq_metal_date', 'unique(metal_id, date)', 'One price per metal and date.')
    ]

    @api.model
    def export_prices_csv(self, start_date=None, end_date=None, metal_ids=None):
        """Return a CSV string with one row per day and one column per metal."""

        def _to_date(value):
            if not value:
                return None
            if isinstance(value, str):
                return fields.Date.from_string(value)
            if isinstance(value, date):
                return value
            if hasattr(value, "date"):
                return value.date()
            raise ValueError(f"Unsupported date value: {value!r}")

        domain = []
        normalized_start = _to_date(start_date)
        normalized_end = _to_date(end_date)
        if normalized_start:
            domain.append(("date", ">=", normalized_start))
        if normalized_end:
            domain.append(("date", "<=", normalized_end))
        if metal_ids:
            domain.append(("metal_id", "in", metal_ids))

        records = self.search(domain, order="date asc, metal_id")
        if not records:
            return ""

        metal_sequence = []
        seen_metals = set()
        for rec in records:
            if rec.metal_id.id in seen_metals:
                continue
            seen_metals.add(rec.metal_id.id)
            metal_sequence.append(rec.metal_id)

        per_day = {}
        for rec in records:
            per_day.setdefault(rec.date, {})[rec.metal_id.id] = rec.price

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["date"] + [m.name for m in metal_sequence])
        for target_date in sorted(per_day.keys()):
            formatted_date = target_date.strftime("%d-%m-%Y")
            row = [formatted_date]
            for metal in metal_sequence:
                value = per_day[target_date].get(metal.id)
                row.append(float(value) if value is not None else "")
            writer.writerow(row)

        return buffer.getvalue()


class MarketSource(models.Model):
    _name = "pdp.market.source"
    _description = "Spot price source"

    name = fields.Char(required=True)
    type = fields.Selection([('manual','Manual'), ('csv','CSV'), ('api','API')], default='manual')
    config_json = fields.Text()