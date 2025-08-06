import os
import sys
import csv
import sys
import re


from ..tools.parsing import safe_float, safe_int, safe_str
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
    
    models = set()

    # Margins
    if everything or "margin" in sys.argv:

        model_name="pdp.margin"
        csv_name="Margins.csv"
        actual_field=[
            "code", "name", "overAllMargins", "parts_margin", "labor_margin", "casting_margin", "stone_margin"
        ]
        fieldnames=[
            "id", "code", "name", "over_all_margins", "parts_margin", "labor_margin", "casting_margin", "stone_margin"
        ]    
        
        def row_to_dict(row):
            
            return {
                "id": func_index(row[0], model_name),
                "code": row[0], 
                "name": row[1], 
                "over_all_margins": float(row[2]), 
                "parts_margin": float(row[3]), 
                "labor_margin": float(row[4]), 
                "casting_margin": float(row[5]), 
                "stone_margin": float(row[6])
            }        
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


    # Metal Margins
    
    if everything or "metal" in sys.argv:
        model_name="pdp.margin.metal"
        csv_name="MetalMargins.csv"
        actual_field=[
            "margin_code", "prod_cat_id(toDEL)", "purity", "margin"
        ]
        fieldnames=[
            "id", "margin_code", "purity", "margin"
        ]
        
        def row_to_dict(row):
            
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "margin_code": row[0], 
                "purity": row[2], 
                "margin": float(row[3])
            }              
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


    # Stone Margins
    if everything or "stone" in sys.argv:
        model_name="pdp.margin.stone"
        csv_name="StoneMargins.csv"
        actual_field=[
            "margin_code", "prod_cat_id(toDEL)", "purity", "margin"
        ]
        fieldnames=[
            "id", "margin_code", "purity", "margin"
        ]
        
        def row_to_dict(row):
            
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "margin_code": row[0], 
                "purity": row[2], 
                "margin": float(row[3])
            }              
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)



    # Addon Margin
    
    if everything or "addon_margin" in sys.argv:
        model_name = "pdp.margin.addon"
        csv_name = "MiscMargins.csv"

        fieldnames = [
            "id", "type_code", "margin_code", "cost"
            ]
        
        def row_to_dict(row):
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "type_code": row[0],
                "margin_code": row[1],
                "cost": safe_float(row[2]),
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


    # ADDON, Metal, Stone, Parts, labor

    # Prices
    if (everything or "price" in sys.argv) and False:
        model_name = "pdp.price"
        csv_name = "Prices.csv"

        fieldnames = [
            "id", "product", "margin_id", "design", "design2", "purity", "currency", "metal_convto",
            "metal_cost", "metal_price", "metal_margin",
            "stone_cost", "stone_price", "stone_margin",
            "parts_cost", "parts_price", "parts_margin",
            "misc_cost", "misc_price", "misc_margin",
            "misc_cost2", "misc_price2", "misc_margin2",
            "labor_cost", "labor_price", "labor_margin",
            "cost", "price", "margin",
            "cost2", "price2", "margin2",
            "m_cost", "m_margin", "m_price",
            "m_metal_cost", "m_metal_margin", "m_metal_price",
            "m_stone_cost", "m_stone_margin", "m_stone_price",
            "m_labor_cost", "m_labor_margin", "m_labor_price",
            "m_parts_cost", "m_parts_margin", "m_parts_price",
            "m_misc_cost", "m_misc_margin", "m_misc_price",
            "int_pric"
        ]
        def row_to_dict(row):
            if row[1] != row[2]:
                row[1] = re.sub(r" ", "", row[1])
                row[2] = re.sub(r" ", "", row[2])
                
                code, stones1 = row[1].split("-")
                stones1 = stones1.split("+")
                
                if stones1[-1] == "W":
                    del stones1[-1]
                stones = stones1 + [row[2]]
                product_code = f"{code}-{'+'.join(stones)}"
                        
                print(product_code)
            else:
                product_code = row[1]
                
            return {
                "id": func_index(f"{row[0]}_{row[1]}_{row[2]}", model_name),
                "product": product_code,
                "margin_id": row[0],
                "design": row[1],
                "design2": row[2],
                "purity": row[3],
                "currency": row[4],
                "metal_convto": row[5],
                "metal_cost": safe_float(row[6]),
                "metal_price": safe_float(row[7]),
                "metal_margin": safe_float(row[8]),
                "stone_cost": safe_float(row[9]),
                "stone_price": safe_float(row[10]),
                "stone_margin": safe_float(row[11]),
                "parts_cost": safe_float(row[12]),
                "parts_price": safe_float(row[13]),
                "parts_margin": safe_float(row[14]),
                "misc_cost": safe_float(row[15]),
                "misc_price": safe_float(row[16]),
                "misc_margin": safe_float(row[17]),
                "misc_cost2": safe_float(row[18]),
                "misc_price2": safe_float(row[19]),
                "misc_margin2": safe_float(row[20]),
                "labor_cost": safe_float(row[21]),
                "labor_price": safe_float(row[22]),
                "labor_margin": safe_float(row[23]),
                "cost": safe_float(row[24]),
                "price": safe_float(row[25]),
                "margin": safe_float(row[26]),
                "cost2": safe_float(row[27]),
                "price2": safe_float(row[28]),
                "margin2": safe_float(row[29]),
                "m_cost": safe_float(row[30]),
                "m_margin": safe_float(row[31]),
                "m_price": safe_float(row[32]),
                "m_metal_cost": safe_float(row[33]),
                "m_metal_margin": safe_float(row[34]),
                "m_metal_price": safe_float(row[35]),
                "m_stone_cost": safe_float(row[36]),
                "m_stone_margin": safe_float(row[37]),
                "m_stone_price": safe_float(row[38]),
                "m_labor_cost": safe_float(row[39]),
                "m_labor_margin": safe_float(row[40]),
                "m_labor_price": safe_float(row[41]),
                "m_parts_cost": safe_float(row[42]),
                "m_parts_margin": safe_float(row[43]),
                "m_parts_price": safe_float(row[44]),
                "m_misc_cost": safe_float(row[45]),
                "m_misc_margin": safe_float(row[46]),
                "m_misc_price": safe_float(row[47]),
                "int_pric": safe_int(row[48])
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


