from odoo import models, fields

class LaborTypes(models.Model):
    _name = 'pdp.labor.type'
    _description = 'Labor Types'
    _rec_name = 'code'

    code = fields.Char(string='Labor Types Code', required=True, index=True)
    name = fields.Char(string='Labor Types Name', required=True)


    def _get_category(self):
        """Return the category of the labor type."""
        if self.code in {'CAS', 'FIL', 'POL'}:
            return 'METAL'
        elif self.code in {'ASS', 'SET'}:
            return  