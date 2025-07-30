import os
import sys
import csv
import sys
import re

from rubicon_import.tools.parsing import safe_float, safe_int, safe_str
from rubicon_import.tools.standard import func_index, size_field
from rubicon_import.raw_to_data.raw_to_data import raw_to_data
     

     
if __name__ == '__main__':
    # Examples for pdp module
    everything = True
    if len(sys.argv) > 1:
        everything = False
        print(f"Begin generation for {sys.argv[1:]}")
    
    
    # Type
    if everything or "type" in sys.argv:
        model_name = "pdp.stone.type"
        csv_name = "StoneTypes.csv"
        fieldnames = ["id", "code", "name", "density", "category_code"]
        def row_to_dict_type(row):
            if row[4] == "": row[4] = 0.0
            density = float(row[4]) * 2.65
            return {
                "id" : func_index(row[0], model_name),
                "code" : row[0],
                "name" : row[1],
                "density" : density,
                "category_code" : row[3],
                # "category_id" : func_index(row[3], "pdp.stone.category"),
            }
        
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict_type)
    
    # Category
    if everything or "category" in sys.argv:

        model_name = "pdp.stone.category"
        csv_name = "StoneCategories.csv"
        fieldnames = ["id", "code", "name"]
        def row_to_dict_cat(row):
            return {
                "id" : func_index(row[0], model_name),
                "code" : row[0],
                "name" : row[1],
                }
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict_cat)
    
    # Size
    if everything or "size" in sys.argv:

        model_name = "pdp.stone.size"
        csv_name = "StoneSizes.csv"
        fieldnames = ["size"]
        def row_to_dict(row):
            return {
                "id": func_index(row[0], model_name),
                "size": size_field(row[0])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    # Shade
    if everything or "shade" in sys.argv:

        model_name = "pdp.stone.shade"
        csv_name = "StoneShades.csv"
        fieldnames = ["code", "shade"]
        def row_to_dict(row):
            return {
                "id": func_index(row[0], model_name),
                "code": row[0],
                "shade": row[1]
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        
    # Shape
    if everything or "shape" in sys.argv:

        model_name = "pdp.stone.shape"
        csv_name = "StoneShapes.csv"
        fieldnames = ["code", "shape"]
        def row_to_dict(row):
            return {
                "id": func_index(row[0], model_name),
                "code": row[0],
                "shape": row[1]
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    # Weight
    if everything or "weight" in sys.argv:
        model_name = "pdp.stone.weight"
        csv_name = "StoneWeights.csv"
        fieldnames = ["weight", "type_code", "shape_code", "shade_code", "size"]
        
        def row_to_dict(row):
            return {
                "id" : 0,
                "type_code": row[0],
                "shape_code" : row[1],
                "shade_code" : row[2],
                "size" : size_field(row[3]),
                "weight": row[4]
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, index_auto=True)
        
    if everything or "stone" in sys.argv:
        model_name = "pdp.stone"
        csv_name = "StoneLots.csv"
        fieldnames = ["id", "code", "type_code", "shape_code", "shade_code", "size", "cost"]
        def row_to_dict(row):
            if row[5] == "":
                row[5] = 0.0
            row[5] = float(row[5])
            if row[6] != "US":
                row[5] *= 0.031 # conv bath -> dollar
            
            return {
                "id" : func_index(row[7], model_name),
                "code" : row[7].upper(),
                "type_code": row[0].upper(),
                "shape_code" : row[1].upper(),
                "shade_code" : row[2].upper(),
                "size" : size_field(row[3]),
                "cost" : row[5],
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
