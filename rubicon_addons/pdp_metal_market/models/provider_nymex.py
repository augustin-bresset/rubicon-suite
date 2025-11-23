"""NY metals market provider using an external API.

This provider pulls daily prices (USD / troy ounce) from a configurable
New York market endpoint and stores them as ``pdp.market.price`` entries.
"""
from datetime import date as date_cls
from typing import Dict, Iterable, List

import os

import requests

from odoo import fields, models
from odoo.exceptions import UserError

METALPRICE_BASE_URL = "https://api.metalpriceapi.com/v1"
METALPRICE_API_KEY = os.getenv("API_KEY_METAL_MARKET")

test_values = {
    "XAU": 4064.9216770891,
    "XAG": 49.9913197572,
    "XPT": 1516.3825420698,
    "XPD": 1381.9184538212,
}



class MarketProviderNY(models.AbstractModel):
    _name = "pdp.market.provider.nymex"
    _description = "New York market API provider"

    # -- Public API ---------------------------------------------------------
    def update_prices(self, codes: Iterable[str] = None, day=None):
        """Fetch and upsert daily spot prices for the given metal codes.

        :param codes: optional iterable of ``pdp.market.metal.code`` values. If
            omitted, every metal is synced.
        :param day: optional date/datetime/str. Defaults to today (server date).
        :return: recordset of ``pdp.market.price`` created or updated.
        """
        target_date = self._normalize_date(day)
        metals = self._metals_to_sync(codes)
        if not metals:
            return self.env["pdp.market.price"]

        code_list = [m.code for m in metals]
        raw_prices = self._fetch_remote(code_list, target_date)
        source = self._get_source()

        results = self.env["pdp.market.price"]
        for metal in metals:
            price_value = raw_prices.get(metal.code)
            if price_value is None:
                continue
            values = {
                "metal_id": metal.id,
                "date": target_date,
                "price": price_value,
                "source_id": source.id,
            }
            existing = results.search([
                ("metal_id", "=", metal.id),
                ("date", "=", target_date),
            ], limit=1)
            if existing:
                existing.write(values)
                results |= existing
            else:
                results |= results.create(values)
        return results

    # -- Helpers ------------------------------------------------------------
    def _metals_to_sync(self, codes: Iterable[str]):
        domain = []
        if codes:
            domain.append(("code", "in", list(codes)))
        return self.env["pdp.market.metal"].search(domain)

    def _normalize_date(self, value):
        if not value:
            return fields.Date.today()
        if isinstance(value, str):
            return fields.Date.from_string(value)
        if isinstance(value, date_cls):
            return value
        if hasattr(value, "date"):
            return value.date()
        raise UserError("Unsupported date value: %r" % value)

    def _get_source(self):
        Source = self.env["pdp.market.source"].sudo()
        source = Source.search([("name", "=", "NY Metals API")], limit=1)
        if not source:
            source = Source.create({
                "name": "NY Metals API",
                "type": "api",
            })
        return source

    def _fetch_remote(self, codes: List[str], target_date):
        raw_rates = self._get_metal_prices(target_date, test=True)
        payload = {"rates": {}}
        for code in codes:
            upper_code = code.upper()
            value = raw_rates.get(upper_code)
            if value is None:
                continue
            payload["rates"][upper_code] = {"price": value}
        return self._normalize_payload(payload)

    def _get_metal_prices(self, target_date=None, test=True) -> Dict[str, float]:
        """Return spot prices per metal code (USD per troy ounce)."""

        if test:
            return test_values

        if not METALPRICE_API_KEY:
            raise UserError("Missing API_KEY_METAL_MARKET in environment")

        date_fragment = "latest" if target_date is None else target_date.isoformat()
        endpoint = f"{METALPRICE_BASE_URL}/{date_fragment}"
        params = {
            "api_key": METALPRICE_API_KEY,
            "base": "USD",
            "currencies": "XAU,XAG,XPT,XPD",
        }

        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise UserError(f"Metal price API error: {data}")

        rates = data.get("rates", {})
        return {
            "XAU": rates.get("USDXAU"),
            "XAG": rates.get("USDXAG"),
            "XPT": rates.get("USDXPT"),
            "XPD": rates.get("USDXPD"),
        }

    def _normalize_payload(self, payload) -> Dict[str, float]:
        """Convert provider JSON payload to {code: price} mapping."""
        rates = payload.get("rates", {}) if isinstance(payload, dict) else {}
        normalized = {}
        for code, entry in rates.items():
            if entry is None:
                continue
            value = entry.get("price") if isinstance(entry, dict) else entry
            try:
                normalized[code.upper()] = float(value)
            except (TypeError, ValueError):
                continue
        return normalized