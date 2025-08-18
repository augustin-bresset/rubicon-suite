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
            code = strip_code_space(row[0])       
            return {
                "id": func_index(code, model_name),
                "code": code, 
                "name": row[1]
            }        
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)

    
    # Margin Labor
    if everything or "labor" in sys.argv:

        model_name="pdp.margin.labor"
        csv_name="Margins.csv"

        fieldnames=[
            "id", "margin_id", "rate_parts", "rate_metal", "rate_stone"
        ]    
        
        def row_to_dict(row):
            margin_code = strip_code_space(row[0])
            return {
                "id": func_index(margin_code, model_name),
                "margin_id": margin_code, 
                "rate_parts": safe_float(row[4]), 
                "rate_metal": safe_float(row[4]), 
                "rate_stone": safe_float(row[6])
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
        actual_field=[
            "margin_code", "prod_cat_id(toDEL)", "stone_type", "stone_shape", "stone_size", "stone_shade", "rate"
        ]
        fieldnames=[
            "id", "margin_id", "stone_type_id", "stone_size_id", "stone_shade_id", "rate"
        ]
        
        def row_to_dict(row):
            margin_code = strip_code_space(row[0])
            stone_type_code = strip_code_space(row[2])
            return {
                "id": func_index(f"{margin_code}_{stone_type_code}", model_name),
                "margin_id": margin_code, 
                "stone_type_id": stone_type_code, 
                "rate": float(row[6])
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


