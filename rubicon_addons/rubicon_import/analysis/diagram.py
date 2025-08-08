# --- SETTINGS ---------------------------------------------------------------
OUTPUT_PATH = "/var/lib/odoo/odoo_erd.puml"
MODEL_NAME_PREFIXES = ["pdp."]  # filtre: ex. ["pdp.", "sale.", "account."]; [] = tout
INCLUDE_TECHNICAL = False       # True pour inclure les modèles techniques/transient
MAX_FIELDS_PER_CLASS = 40       # évite les classes énormes
# ---------------------------------------------------------------------------

from collections import defaultdict

def _want_model(m):
    if not INCLUDE_TECHNICAL and (getattr(m, "transient", False) or getattr(m, "abstract", False)):
        return False
    if not MODEL_NAME_PREFIXES:
        return True
    return any(m.model.startswith(p) for p in MODEL_NAME_PREFIXES)

def _ptype(f):
    # Types simples: on affiche court
    t = f.ttype
    if t == "many2one":
        return f"m2o→{f.relation}"
    if t == "one2many":
        return f"o2m→{f.relation}"
    if t == "many2many":
        return f"m2m→{f.relation}"
    if t == "selection":
        return "selection"
    return t

def export_erd(env):
    IrModel = env["ir.model"]
    IrField = env["ir.model.fields"]
    all_models = IrModel.search([])
    models = [m for m in all_models if _want_model(m)]
    model_by_name = {m.model: m for m in models}
    model_labels = {}  # "pdp.product" -> 'pdp.product' (garde le label tel quel)
    # Prépare les champs par modèle
    fields_by_model = defaultdict(list)
    rel_edges = []  # tuples: (src_model, dst_model, kind, field_name)
    # Récupérer tous les champs en une fois pour perf
    all_fields = IrField.search([('model_id', 'in', [m.id for m in models])])
    for f in all_fields:
        mname = f.model
        if mname not in model_by_name:
            continue
        fields_by_model[mname].append(f)
        if f.ttype in ("many2one", "one2many", "many2many") and f.relation:
            # On ne dessine des arêtes que si la cible existe dans notre sous-ensemble
            if f.relation in model_by_name:
                kind = {"many2one": "m2o", "one2many": "o2m", "many2many": "m2m"}[f.ttype]
                rel_edges.append((mname, f.relation, kind, f.name))
    # --- Génération PlantUML ---
    lines = []
    lines.append("@startuml")
    lines.append("skinparam classAttributeIconSize 0")
    lines.append("hide circle")
    lines.append("hide methods")
    # Classes
    for m in sorted(models, key=lambda x: x.model):
        mlabel = m.model
        model_labels[m.model] = mlabel
        lines.append(f'class "{mlabel}" as {mlabel.replace(".", "_")} {{')
        # id implicite
        lines.append("  + id : integer")
        # champs (on tronque si trop long)
        displayed = 0
        for f in sorted(fields_by_model[m.model], key=lambda x: (x.ttype, x.name)):
            # On évite les x2many inverse spé vraiment verbeux
            if displayed >= MAX_FIELDS_PER_CLASS:
                lines.append("  ...")
                break
            display = f"- {f.name} : " + _ptype(f)
            lines.append("  " + display)
            displayed += 1
        lines.append("}")
    # Relations
    # m2o: solid arrow --> ; m2m: dashed -- ; o2m: dotted ..>
    for src, dst, kind, fname in sorted(set(rel_edges)):
        s = src.replace(".", "_")
        d = dst.replace(".", "_")
        label = fname
        if kind == "m2o":
            lines.append(f"{s} --> {d} : {label}")
        elif kind == "m2m":
            lines.append(f"{s} -- {d} : {label}")
        else:  # o2m
            lines.append(f"{s} ..> {d} : {label} (o2m)")
    lines.append("@enduml")
    # Écriture
    import os
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return OUTPUT_PATH

path = export_erd(env)
print(f"[OK] ERD exporté → {path}")
