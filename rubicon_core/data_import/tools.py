import os
import csv

from sqlalchemy.orm import Session
from rubicon_core.db import engine

from rubicon_core.data_import.mapping import (
    mapping_stone_category_csv, mapping_stone_shade_csv, mapping_stone_shape_csv, mapping_stone_size_csv, 
    mapping_stone_type_csv, mapping_tablename_csv)

from rubicon_core.models.reference import (
    StoneCategory, StoneShade, StoneShape, StoneSize, StoneType
)

def import_csv(model, mapping, delimiter=','):
    """
    Importe un CSV *sans header* selon :
      - model   : classe SQLAlchemy (ex. StoneType)
      - path    : chemin vers le fichier CSV
      - fields  : liste/tuple des noms de champs (ou None) dans l'ordre des colonnes
      - processor(row: dict, session) -> instance de model (optionnel)
      - delimiter : séparateur du CSV (par défaut ',')
    Retourne la liste des instances créées.
    """
    session = Session(bind=engine)
    created = []
    
    path        = mapping.get("path")
    fields      = tuple(mapping.get("fields"))
    key_fields  = tuple(mapping.get("key_fields"))
    processor   = mapping.get("processor")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for values in reader:
            # zip avec fields pour obtenir un dict {field: raw_value}
            row = {
                field: val.strip()
                for field, val in zip(fields, values)
                if field is not None
            }
            q = session.query(model)
            for k in key_fields:
                q = q.filter(getattr(model, k) == row[k])
            instance = q.one_or_none() if key_fields else None

            if not instance:
                if processor:
                    obj = processor(row, session)

                else:
                    kwargs = {
                        k: row[k]
                        for k in row
                        if hasattr(model, k)
                    }
                    obj = model(**kwargs)
                if obj is not None:
                    session.add(obj)
                    created.append(obj)

    session.commit()
    session.close()
    return created



if __name__=="__main__":
    import_csv(StoneCategory, mapping_stone_category_csv)
    import_csv(StoneType, mapping_stone_type_csv)
    import_csv(StoneSize, mapping_stone_size_csv)
    import_csv(StoneShape, mapping_stone_shape_csv)
    import_csv(StoneShade, mapping_stone_shade_csv)
    