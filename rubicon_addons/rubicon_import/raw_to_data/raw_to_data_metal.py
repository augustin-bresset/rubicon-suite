import os
import sys
import csv
import sys


from ..tools.parsing import safe_float, safe_int, safe_str
from ..tools.standard import func_index, strip_code_space, mapping_currency
from .raw_to_data import raw_to_data
        

if __name__ == '__main__':
    # Examples for pdp module
    everything = True
    if len(sys.argv) > 1:
        everything = False
        print(f"Begin generation for {sys.argv[1:]}")
    
    # Purity
    if everything or "purity" in sys.argv:
        model_name="pdp.metal.purity"
        csv_name = "MetalPurities.csv"
        fieldnames = ["id", "code", "percent"]
        def row_to_dict(row):
            code = strip_code_space(row[0])
            return {
                "id": func_index(code, model_name),
                "code": code,
                "percent": safe_float(row[1])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_metal')
        
    # Metal
    if everything or "metal" in sys.argv:
        model_name="pdp.metal"
        csv_name = "Metals.csv"
        fieldnames = ["id", "code", "name", "cost", "currency_id", "reference", "gold", "plating"]
        def row_to_dict(row):
            
            code = strip_code_space(row[0])
            
            reference = False
            gold = False
            if row[0] == "W " : 
                reference = True
            if "gold" in row[1].lower():
                gold = True 
            
            return {
                "id": func_index(code, model_name),
                "code": code,
                "name": row[1],
                "cost": float(row[2]),
                "currency_id": mapping_currency(row[3], default="USD"),
                "gold": gold,
                "plating": bool(int(row[4])),
                "reference": reference,
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_metal')
        
    # Part
    if everything or "part" in sys.argv:
        model_name="pdp.part"
        csv_name = "Parts.csv"
        fieldnames = ["id", "code", "name"]
        def row_to_dict(row):
            code = strip_code_space(row[0])
            return {
                "id": func_index(code, model_name),
                "code": code,
                "name": row[1],
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_metal')
        
    # Part Cost
    if everything or "part_cost" in sys.argv:
        model_name="pdp.part.cost"
        csv_name = "PartsCost.csv"
        fieldnames = ["id", "part_id", "purity_id", "cost", "currency_id"]
        def row_to_dict(row):
            part_code = strip_code_space(row[0])
            purity_code = strip_code_space(row[1])
            return {
                "id": func_index(f"{part_code}_{purity_code}", model_name),
                "part_id": part_code,
                "purity_id" : purity_code,
                "cost": safe_float(row[2]),
                "currency_id" : mapping_currency(row[3])
                
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_metal')
        