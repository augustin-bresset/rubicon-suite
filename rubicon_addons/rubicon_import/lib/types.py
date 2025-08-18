from odoo import fields as odoo_fields
from .m2o import resolve_many2one
from .utils import is_empty

def fields_type_to_func(env, field, value):
    """Conversion générique par type de champ Odoo."""
    if is_empty(value):
        return None
    if isinstance(field, odoo_fields.Float):
        return float(value)
    if isinstance(field, odoo_fields.Integer):
        return int(value)
    if field.type == 'many2one':
        return resolve_many2one(env, field, value)
    return value
