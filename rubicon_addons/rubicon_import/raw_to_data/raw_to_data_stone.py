import os
import sys
import csv
import sys
import re

from rubicon_import.tools.parsing import safe_float, safe_int, safe_str, no_all_one_zero_value
from rubicon_import.tools.standard import func_index, size_field, strip_code_space, mapping_currency, create_stone_code
from rubicon_import.raw_to_data.raw_to_data import raw_to_data
     

     
if __name__ == '__main__':
    # Examples for pdp module
    everything = True
    if len(sys.argv) > 1:
        everything = False
        print(f"Begin generation for {sys.argv[1:]}")
    
    # Category
    if everything or "category" in sys.argv:

        model_name = "pdp.stone.category"
        csv_name = "StoneCategories.csv"
        fieldnames = ["id", "code", "name"]
        def row_to_dict_cat(row):
            code = strip_code_space(row[0])
            if row[1] in {"ALL", "all", "1", "0"}:
                return
            return {
                "id" : func_index(code, model_name),
                "code" : code,
                "name" : row[1],
                }
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict_cat, dest_folder='pdp_stone')
    
    # Type
    if everything or "type" in sys.argv:
        model_name = "pdp.stone.type"
        csv_name = "StoneTypes.csv"
        fieldnames = ["id", "code", "name", "density", "category_id"]
        def row_to_dict(row):
            if row[4] == "": row[4] = 0.0
            density = float(row[4]) * 2.65
            code = strip_code_space(row[0])
            category_id = no_all_one_zero_value(strip_code_space(row[3]))
            return {
                "id" : func_index(code, model_name),
                "code" : code,
                "name" : row[1],
                "density" : density,
                "category_id" : category_id,
            }
        
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_stone')
    
    
    
    # Size
    if everything or "size" in sys.argv:

        model_name = "pdp.stone.size"
        csv_name = "StoneSizes.csv"
        fieldnames = ["name"]
        def row_to_dict(row):
            return {
                "id": func_index(row[0], model_name),
                "name": size_field(row[0])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_stone')
    
    # Shade
    if everything or "shade" in sys.argv:

        model_name = "pdp.stone.shade"
        csv_name = "StoneShades.csv"
        fieldnames = ["code", "shade"]
        def row_to_dict(row):
            code = strip_code_space(row[0])
            if row[1] in {"ALL", "all", "1", "0"}:
                return
            return {
                "id" : func_index(code, model_name),
                "code" : code,
                "shade": row[1]
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        
    # Shape
    if everything or "shape" in sys.argv:

        model_name = "pdp.stone.shape"
        csv_name = "StoneShapes.csv"
        fieldnames = ["code", "shape"]
        def row_to_dict(row):
            code = strip_code_space(row[0])
            return {
                "id" : func_index(code, model_name),
                "code" : code,
                "shape": row[1]
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_stone')
    
    # Weight
    if everything or "weight" in sys.argv:
        model_name = "pdp.stone.weight"
        csv_name = "StoneWeights.csv"
        fieldnames = ["weight", "type_id", "shape_id", "shade_id", "size_id"]
        
        
        def row_to_dict(row):
            type_code = strip_code_space(row[0])
            shape_code = strip_code_space(row[1])
            shade_code = no_all_one_zero_value(strip_code_space(row[2]))
            weight = safe_float(row[4])
            if weight == 0.0:
                return 
            return {
                "id" : 0,
                "type_id": type_code,
                "shape_id" : shape_code,
                "shade_id" : shade_code,
                "size_id" : size_field(row[3]),
                "weight": weight
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, index_auto=True, dest_folder='pdp_stone')
    
    # Stone
    if everything or "stone" in sys.argv:
        model_name = "pdp.stone"
        csv_name = "StoneLots.csv"
        fieldnames = ["id", "code", "type_id", "shape_id", "shade_id", "size_id", "cost", "currency_id"]
    
        def case_management(row):
            return row[7] == 'SKLD-RDCAB-4' 
        
        def row_to_dict(row):
            if row[5] == "":
                row[5] = 0.0
            if case_management(row):
                return 
            
            row[5] = float(row[5])
            # if row[6] != "US":
            #     row[5] *= 0.031 # conv bath -> dollar
            code = strip_code_space(row[7])
            type_code = strip_code_space(row[0])
            shape_code = strip_code_space(row[1])
            shade_code = no_all_one_zero_value(strip_code_space(row[2]))
            

            size = size_field(row[3])
            
            stone_code = create_stone_code(type_code, shade_code, shape_code, size)
            return {
                "id" : func_index(row[7], model_name),
                "code" : stone_code,
                "type_id": type_code,
                "shape_id" : shape_code,
                "shade_id" : no_all_one_zero_value(shade_code),
                "size_id" : size,
                "cost" : safe_float(row[5]),
                "currency_id": mapping_currency(row[6])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_stone')
