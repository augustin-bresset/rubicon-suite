# Cache M2O mutualisé
_many2one_cache = {}

def reset_m2o_cache():
    global _many2one_cache
    _many2one_cache = {}

def resolve_many2one(env, field, raw_value):
    """
    Résout un Many2one par rec_name exact, via cache.
    (Même comportement que ton code “simple” actuel.)
    """
    from .utils import is_empty
    comodel = field.comodel_name
    rec_name = env[comodel]._rec_name
    if is_empty(raw_value):
        return None
    raw = str(raw_value).strip()

    # init cache
    global _many2one_cache
    if comodel not in _many2one_cache:
        print(f"[INFO] Loading {comodel} references via `{rec_name}`...")
        _many2one_cache[comodel] = {
            str(r[rec_name]).strip(): r.id
            for r in env[comodel].search([])
        }

    hit = _many2one_cache[comodel].get(raw)
    if hit is None:
        print(f"[WARN] Unresolved Many2one: {field.name} = '{raw}' in {comodel} using {rec_name}")
    return hit
