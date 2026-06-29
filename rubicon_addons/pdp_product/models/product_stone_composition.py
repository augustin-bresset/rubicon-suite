from odoo import models, fields, api

class ProductStoneComposition(models.Model):
    _name = 'pdp.product.stone.composition'
    _description = 'Group of stones used in a product (without metal)'
    _rec_name = 'code'

    code = fields.Char(string='Composition Code', required=True, index=True)
    
    stone_line_ids = fields.One2many(
        comodel_name='pdp.product.stone',
        inverse_name='composition_id',
        string='Stone Lines'
    )

    # =========================================================================
    # Domain Methods - Reusable by API, Cron, OWL, Reports
    # =========================================================================

    def to_dict_list(self):
        """Return all stone lines as list of dicts."""
        self.ensure_one()
        return [line.to_dict() for line in self.stone_line_ids]

    def get_weight_summary(self):
        """Compute total weight and pieces for this composition."""
        self.ensure_one()
        total_weight = 0.0
        total_pieces = 0
        for line in self.stone_line_ids:
            total_pieces += line.pieces
            w = line.weight or 0.0
            total_weight += w * line.pieces
        return {
            'total_weight': total_weight,
            'total_pieces': total_pieces,
        }

    # =========================================================================
    # Colour code computation
    # =========================================================================

    @staticmethod
    def _line_weight(line):
        """Per-stone weight retained for ordering: reshaped if present, else
        the original (purchased) weight."""
        return line.reshaped_weight if line.reshaped_weight else (line.weight or 0.0)

    @staticmethod
    def _order_color_codes(entries):
        """Order stone type codes from ``(code, weight, is_center)`` tuples.

        Center code first (if any), then by heaviest single weight descending,
        tie broken by code ascending. Entries with a falsy code are ignored.
        Returns the ordered list of distinct codes.
        """
        max_by_type = {}
        center_code = None
        for code, weight, is_center in entries:
            if not code:
                continue
            if code not in max_by_type or weight > max_by_type[code]:
                max_by_type[code] = weight
            if is_center:
                center_code = code
        if not max_by_type:
            return []
        ordered = sorted(
            (code for code in max_by_type if code != center_code),
            key=lambda code: (-max_by_type[code], code),
        )
        if center_code:
            ordered = [center_code] + ordered
        return ordered

    def compute_color_code(self):
        """Return the ordered, '+'-joined distinct stone TYPE codes.

        Ordering rule:
          1. the center stone's type first (if a line is flagged is_center);
          2. then the remaining types by heaviest single stone, descending;
          3. ties broken by type code, ascending (deterministic).

        Lines whose stone has no type are ignored. An empty composition
        returns ''.
        """
        self.ensure_one()
        entries = [
            (line.stone_id.type_id.code, self._line_weight(line), line.is_center)
            for line in self.stone_line_ids
        ]
        return '+'.join(self._order_color_codes(entries))

    @api.model
    def color_code_from_line_data(self, line_data):
        """Colour code from raw workspace rows, without persisting anything.

        ``line_data`` is a list of dicts with ``type_id`` (int), ``weight``,
        ``reshaped_weight`` and ``is_center``. Lets the OWL workspace preview
        the colour code live, reflecting unsaved edits, through the same
        ordering logic as the stored compute.
        """
        type_ids = [d['type_id'] for d in line_data if d.get('type_id')]
        code_by_id = {
            t.id: t.code for t in self.env['pdp.stone.type'].browse(type_ids)
        }
        entries = [
            (
                code_by_id.get(d.get('type_id')),
                d.get('reshaped_weight') or d.get('weight') or 0.0,
                bool(d.get('is_center')),
            )
            for d in line_data
        ]
        return '+'.join(self._order_color_codes(entries))

    @api.model
    def suggest_from_line_data(self, line_data, model_code=None, metal=None):
        """Return ``{'colors', 'product_code'}`` suggested for the given rows."""
        colors = self.color_code_from_line_data(line_data)
        return {
            'colors': colors,
            'product_code': self.build_product_code(model_code, colors, metal),
        }

    @staticmethod
    def build_composition_code(model_code, colors):
        """Composition code = '{model}-{colors}' (just the model if no colors)."""
        model_code = model_code or ''
        return f"{model_code}-{colors}" if colors else model_code

    @staticmethod
    def build_product_code(model_code, colors, metal):
        """Product code = '{model}-{colors}/{metal}'."""
        base = ProductStoneComposition.build_composition_code(model_code, colors)
        return f"{base}/{metal}" if metal else base
