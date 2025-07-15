from .processors import process_stone_type

mapping_tablename_csv = {
    "path": "./path/to/csv/file.csv",
    "fields": ("model_field", None, "model_field"),
    "key_fields" : ("key",),
    "processor": None
}


## STONE

mapping_stone_category_csv = {
    "path":"./data/backup_pdp/StoneCategories.csv",
    "fields": ("code", "name", None, None, None, None, None),
    "key_fields" : ("code",)
}


mapping_stone_type_csv = {
    "path":"./data/backup_pdp/StoneTypes.csv",
    "fields": ("code", "name", None, "category_code", "relative_density"),
    "key_fields": ("code",),
    "processor": process_stone_type
}

mapping_stone_size_csv = {
    "path":"./data/backup_pdp/StoneSizes.csv",
    "fields": ("size", ),
    "key_fields": ("size",),
}

mapping_stone_shape_csv = {
    "path":"./data/backup_pdp/StoneShapes.csv",
    "fields": ("code", "name"),
    "key_fields": ("code",),
}

mapping_stone_shade_csv = {
    "path":"./data/backup_pdp/StoneShapes.csv",
    "fields": ("code", "name"),
    "key_fields": ("code",),
}


