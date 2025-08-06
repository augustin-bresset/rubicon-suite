import os
import sys
import csv
import sys
import re


from ..tools.parsing import safe_float, safe_int, safe_str
from ..tools.standard import create_model_code
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
    
    
    
    # Labor Types
    if everything or "labor_type" in sys.argv:
        model_name="pdp.labor.type"
        csv_name = "LaborTypes.csv"
        fieldnames = ["id", "code", "name", "cost"]
            
        def row_to_dict(row):
            if row[0] == "LAB":
                row[0] = "ASS"
                row[1] = "Assembly"
            return {
                "id": func_index(row[0], model_name),
                "code": row[0],
                "name": row[1],
                "cost": float(row[2])
            }
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    
    # Addon type
    
    if everything or "addon_type" in sys.argv:
        model_name = "pdp.addon.type"
        csv_name = "MiscTypes.csv"

        fieldnames = [
            "id", "code", "name"
            ]
        
        def row_to_dict(row):
            return {
                "id": func_index(row[0], model_name),
                "code": row[0],
                "name": row[1]
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)

        
    # Labor product cost
    if everything or "product cost" in sys.argv:
        model_name="pdp.labor.cost.product"
        csv_name = "ProductLaborCost.csv"   
        fieldnames = ["id", "product_code", "labor_code", "cost"]
        def row_to_dict(row):
            
            while len(row) > 4:
                row[0] = f"{row[0]}+{row[1]}"
                for i in range(1, len(row)-1):
                    row[i] = row[i+1]
                del row[-1]
            cost = safe_float(row[3])
            if cost == 0.0:
                return
            if row[1] == "LAB": 
                row[1] = "ASS"
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "product_code": row[0],
                "labor_code": row[1],
                "cost": safe_float(row[3])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    # NEW MODEL COST
    if everything or "model_cost" in sys.argv:
        model_name="pdp.labor.cost.model"
        csv_name = "ModelLabor.csv"
        fieldnames = ["id", "model_code", "metal_code", "labor_code", "cost"]
        def row_to_dict(row):
            if not row[0].isalpha():
                return
            model_code = create_model_code(row[0], row[1])
            metal_code = row[2]
            
            out = {
                "id": None,
                "model_code": model_code,
                "metal_code": metal_code,
                "labor_code": None, "cost": 0.0
                }
            cost = safe_float(row[3])
            if cost > 0.0:
                out["labor_code"] = "ASS"
                out["id"] = func_index(f"{model_code}{metal_code}_ASS", model_name)
                out["cost"] = cost
                yield out
                
            cost = safe_float(row[4])
            if cost > 0.0:

                out["labor_code"] = "CAS"
                out["id"] = func_index(f"{model_code}{metal_code}_CAS", model_name)
                out["cost"] = cost
                yield out
            
            cost = safe_float(row[5])
            if cost > 0.0:

                out["labor_code"] = "FIL"
                out["id"] = func_index(f"{model_code}{metal_code}_FIL", model_name)
                out["cost"] = cost
                yield out
            
            cost = safe_float(row[6])
            if cost > 0.0:
                out["labor_code"] = "POL"
                out["id"] = func_index(f"{model_code}{metal_code}_POL", model_name)
                out["cost"] = cost
                yield out
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    
    # Addon product cost
    if everything or "product cost" in sys.argv:
        model_name="pdp.addon.cost"
        csv_name = "ProductMiscCost.csv"
        fieldnames = ["id", "product_code", "addon_code", "cost"]
        def row_to_dict(row):
            while len(row) > 4:
                row[0] = f"{row[0]}+{row[1]}"
                for i in range(1, len(row)-1):
                    row[i] = row[i+1]
                del row[-1]
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "product_code": row[0],
                "addon_code": row[1],
                "cost": safe_float(row[3])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
