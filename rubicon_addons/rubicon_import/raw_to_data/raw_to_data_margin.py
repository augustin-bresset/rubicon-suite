import os
import sys
import csv
import sys
import re


from ..tools.parsing import safe_bool, safe_float, safe_int, safe_str
from ..tools.standard import strip_code_space
from .raw_to_data import raw_to_data

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
            "id", "code", "name"
            ]    
        
        def row_to_dict(row):            
            return {
                "id": func_index(row[0], model_name),
                "code": row[0], 
                "name": row[1]
            }        
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)

    
    # Margin Labor
    if everything or "labor" in sys.argv:

        model_name="pdp.margin.labor"
        csv_name="Margins.csv"

        fieldnames=[
            "id", "margin_code", "rate_parts", "rate_metal", "rate_stone"
        ]    
        
        def row_to_dict(row):
            
            return {
                "id": func_index(row[0], model_name),
                "margin_code": row[0], 
                "rate_parts": safe_float(row[4]), 
                "rate_metal": safe_float(row[4]), 
                "rate_stone": safe_float(row[6])
            }        
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


    # Metal Margins
    
    if everything or "metal" in sys.argv:
        model_name="pdp.margin.metal"
        csv_name="MetalMargins.csv"
        actual_field=[
            "margin_code", "prod_cat_id(toDEL)", "purity", "rate"
        ]
        fieldnames=[
            "id", "margin_code", "metal_purity_code", "rate"
        ]
        
        def row_to_dict(row):
            metal_purity_code = strip_code_space(row[2])
            return {
                "id": func_index(f"{row[0]}_{metal_purity_code}", model_name),
                "margin_code": row[0], 
                "metal_purity_code": metal_purity_code, 
                "rate": safe_float(row[3])
            }              
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


    # Stone Margins
    if everything or "stone" in sys.argv:
        model_name="pdp.margin.stone"
        csv_name="StoneMargins.csv"
        actual_field=[
            "margin_code", "prod_cat_id(toDEL)", "stone_type", "stone_shape", "stone_size", "stone_shade", "rate"
        ]
        fieldnames=[
            "id", "margin_code", "stone_type_code", "stone_size", "stone_shade", "rate"
        ]
        
        def row_to_dict(row):
            stone_type_code = row[2]
            return {
                "id": func_index(f"{row[0]}_{stone_type_code}", model_name),
                "margin_code": row[0], 
                "stone_type_code": stone_type_code, 
                "rate": float(row[6])
            }              
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


    # Addon Margin    
    if everything or "addon_margin" in sys.argv:
        model_name = "pdp.margin.addon"
        csv_name = "MiscMargins.csv"

        fieldnames = [
            "id", "margin_code", "addon_code", "rate"
            ]
        
        def row_to_dict(row):
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "margin_code": row[1],
                "addon_code": row[0],
                "rate": safe_float(row[2]),
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


