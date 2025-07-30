import os
import sys
import csv
import sys


from ..tools.parsing import safe_float, safe_int, safe_str
from ..tools.standard import func_index
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
            return {
                "id": func_index(row[0], model_name),
                "code": row[0].replace(" ", "").upper(),
                "percent": float(row[1] or '0.0')
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        
    # Metal
    if everything or "metal" in sys.argv:
        model_name="pdp.metal"
        csv_name = "Metals.csv"
        fieldnames = ["id", "code", "name", "cost", "reference", "gold", "plating"]
        def row_to_dict(row):
            reference = False
            gold = False
            if row[0] == "W " : 
                reference = True
            if "gold" in row[1].lower():
                gold = True 
            return {
                "id": func_index(row[0], model_name),
                "code": row[0].replace(' ', ''),
                "name": row[1],
                "cost": float(row[2]),
                "gold": gold,
                "plating": bool(int(row[4])),
                "reference": reference,
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        
    # Part
    if everything or "part" in sys.argv:
        model_name="pdp.part"
        csv_name = "Parts.csv"
        fieldnames = ["id", "code", "name"]
        def row_to_dict(row):
            return {
                "id": func_index(row[0], model_name),
                "code": row[0],
                "name": row[1],
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        
    # Part Cost
    if everything or "part_cost" in sys.argv:
        model_name="pdp.part.cost"
        csv_name = "PartsCost.csv"
        fieldnames = ["id", "part_code", "purity_code", "cost"]
        def row_to_dict(row):
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "part_code": row[0],
                "purity_code" : row[1].replace(" ", "").upper(),
                "cost": float(row[2]),
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        