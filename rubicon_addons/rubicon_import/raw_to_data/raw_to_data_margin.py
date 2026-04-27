import os
import sys
import csv
import sys
import re


from ..tools.parsing import safe_bool, safe_float, safe_int, safe_str
from ..tools.standard import strip_code_space, mapping_currency
from .raw_to_data import raw_to_data, backup_folder

def func_index(code:str, model_name:str):
    model_name = model_name.split(".")[-1]
    code = re.sub(r"[ .-/+-]", "_", code)
    return f"{model_name}_{code}"


if __name__ == '__main__':
    # Examples for pdp module
    everything = True
    if len(sys.argv) > 1:
        everything = False
        print(f"Begin generation for {sys.argv[1:]}")
    
    
    # Margin
    if everything or "code" in sys.argv:

        model_name="pdp.margin"
        csv_name="Margins.csv"

        fieldnames=[
            "id", "code", "name", "labor_metal_rate", "labor_stone_rate"
        ]

        def row_to_dict(row):
            code = strip_code_space(row[0])
            return {
                "id": func_index(code, model_name),
                "code": code,
                "name": row[1],
                "labor_metal_rate": safe_float(row[5]),
                "labor_stone_rate": safe_float(row[7]),
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)
    
    
    
    
    # Margin Part
    if everything or "part" in sys.argv:
        model_name="pdp.margin.part"
        csv_name="Margins.csv"

        fieldnames=[
            "id", "margin_id", "rate"        ]    
        
        def row_to_dict(row):
            margin_code = strip_code_space(row[0])
            return {
                "id": func_index(margin_code, model_name),
                "margin_id": margin_code, 
                "rate": safe_float(row[4]), 
                }        
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)



    # Metal Margins
    
    if everything or "metal" in sys.argv:
        model_name="pdp.margin.metal"
        csv_name="MetalMargins.csv"
        actual_field=[
            "margin_id", "prod_cat_id(toDEL)", "purity_id", "rate"
        ]
        fieldnames=[
            "id", "margin_id", "metal_purity_id", "rate"
        ]
        
        def row_to_dict(row):
            metal_purity_code = strip_code_space(row[2])
            margin_code = strip_code_space(row[0])
            return {
                "id": func_index(f"{margin_code}_{metal_purity_code}", model_name),
                "margin_id": margin_code, 
                "metal_purity_id": metal_purity_code, 
                "rate": safe_float(row[3])
            }              
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)


    # Stone Margins
    if everything or "stone" in sys.argv:
        model_name="pdp.margin.stone"
        csv_name="StoneMargins.csv"
        fieldnames=[
            "id", "margin_id", "stone_type_id", "stone_shape_id",
            "stone_size_id", "stone_shade_id", "rate"
        ]

        def row_to_dict(row):
            margin_code = strip_code_space(row[0])
            stone_type_code = strip_code_space(row[2])
            # col[3] = stone_shape: "1" or "All" means wildcard (no filter)
            shape_raw = strip_code_space(row[3]) if len(row) > 3 else ''
            shape_code = '' if shape_raw in ('', '1', 'All', 'ALL') else shape_raw
            # col[4] = stone_size: "All" means wildcard
            size_raw = strip_code_space(row[4]) if len(row) > 4 else ''
            size_code = '' if size_raw in ('', 'All', 'ALL') else size_raw
            # col[5] = stone_shade: "1" means wildcard
            shade_raw = strip_code_space(row[5]) if len(row) > 5 else ''
            shade_code = '' if shade_raw in ('', '1', 'All', 'ALL') else shade_raw
            return {
                "id": func_index(f"{margin_code}_{stone_type_code}_{shape_code}_{size_code}_{shade_code}", model_name),
                "margin_id": margin_code,
                "stone_type_id": stone_type_code,
                "stone_shape_id": shape_code,
                "stone_size_id": size_code,
                "stone_shade_id": shade_code,
                "rate": float(row[6]),
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)


    # Addon Margin    
    if everything or "addon_margin" in sys.argv:
        model_name = "pdp.margin.addon"
        csv_name = "MiscMargins.csv"

        fieldnames = [
            "id", "margin_id", "addon_id", "rate"
            ]
        
        def row_to_dict(row):
            addon_code = strip_code_space(row[0])
            margin_code = strip_code_space(row[1])
            return {
                "id": func_index(f"{addon_code}_{margin_code}", model_name),
                "addon_id": addon_code,
                "margin_id": margin_code,
                "rate": safe_float(row[2]),
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)


    # Stone Conditional
    if everything or 'conditional' in sys.argv:
        model_name = 'pdp.margin.stone.conditional'
        csv_name = 'StoneMarginsConditional.csv'
        fieldnames = [
            'id', 'margin_id', 'stone_cat_id', 'operator', 'comparative_cost', 'currency_id', 'rate'
        ]
        
        def row_to_dict(row):
            margin_id = strip_code_space(row[0])
            category_id = strip_code_space(row[1])
            operator = strip_code_space(row[2])
            return {
                'id' : func_index(f"{margin_id}_{category_id}", model_name), 
                'margin_id': margin_id, 
                'stone_cat_id': category_id, 
                'operator': operator, 
                'comparative_cost' : safe_float(row[3]), 
                'currency_id': mapping_currency(row[4]),
                'rate' : safe_float(row[5])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)