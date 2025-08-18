from odoo import models, fields


class StoneType(models.Model):
    _name = "pdp.stone.type"
    _description = "Stone Type"
    _rec_name = "code"
    _order = "category_id, code"

    active = fields.Boolean(default=True)
    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True, translate=True)
    density = fields.Float(string="Density (g/cm³)", digits=(16,4))
    category_id = fields.Many2one("pdp.stone.category", string="Category", index=True)

    _sql_constraints = [
        ("code_uniq","unique(code)","Stone Type code must be unique."),
        ("density_nonneg","CHECK (density IS NULL OR density >= 0)","Density must be ≥ 0"),
    ]

    def name_get(self):
        res=[]
        for r in self:
            lbl = f"[{r.code}] {r.name}" if (r.code and r.name) else (r.code or r.name or str(r.id))
            res.append((r.id, lbl))
        return res

    
    def get_referential_density(self):
        """
        Referential with quartz (2.65g/cm3) because of its low variance (~0.005g/cm3)
        """
        return self.density / 2.65