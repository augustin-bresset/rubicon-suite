import os
import sys
import csv
import sys
import re

def func_index(code:str, model_name:str):
    model_name = model_name.split(".")[-1]
    code = re.sub(r"[ .-/+-]", "_", code)
    return f"{model_name}_{code}"

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def safe_str(val):
    if val in {'\x00', None}:
        return ''
    return val
    

root_folder = os.path.join(os.path.dirname(__file__), 'rubicon-suite')
# Folders
backup_folder = os.path.join('data', 'backup_pdp')
data_folder = os.path.join('data', 'odoo')

model_name = "stone.type"

csv_name = "StoneTypes.csv"

def row_to_dict_ex(row):
    return {
        "id" : func_index(row[0], model_name),        
    }

def raw_to_data(model_name, csv_name, fieldnames, row_to_dict, index_auto=False):
    
    dest_name = os.path.join(data_folder, f"{model_name}.csv")
    
    file_name = os.path.join(backup_folder, csv_name)

    if fieldnames[0] != "id":
        fieldnames = ["id"] + fieldnames

    with open(file_name, newline='', encoding='utf-8') as src_file:
        reader = csv.reader(src_file)
        # Prepare header: external id + model_fields
        
        with open(dest_name, 'w', newline="", encoding='utf-8') as dst_file:
            writer = csv.DictWriter(dst_file, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, row in enumerate(reader):
                out = row_to_dict(row)
                if out is not None:                    
                    if index_auto:
                        out["id"] = func_index(str(i), model_name)
                    writer.writerow(out)
    print(f"Generated {dest_name}")




def create_model_code(category, code):
    model_code_ = ''.join((category,code))
    model_code_ = re.sub(r'[ ]', '', model_code_).upper()
    return model_code_

def create_product_code(category, code, stones):
    product_code = f"{category}{code.zfill(3)}-{stones}"    
    return re.sub(r'[ ]', '', product_code)

def create_stone_code(stone_type, stone_shade, stone_shape, size):
    stone_type = stone_type.replace(' ', '')
    stone_shade = stone_shade.replace(' ', '')
    if stone_shade == '1':
        stone_shade = ''
    stone_shape = stone_shape.replace(' ', '')
    if stone_shape == '1':
        stone_shape = ''
    return f"{stone_type}{stone_shade}-{stone_shape}-{size}"

if __name__ == '__main__':
    # Examples for pdp module
    everything = True
    if len(sys.argv) > 1:
        everything = False
        print(f"Begin generation for {sys.argv[1:]}")
    
    models = set()
    # Model
    # BA ,014B ,14,B014B-N-2,
    if everything or "model" in sys.argv:
        model_name="pdp.product.model"
        csv_name = "Models.csv"
        fieldnames = ["id", "code", "category_code", "parent_model_code", "drawing", "quotation"]
        def row_to_dict(row):
            code = create_model_code(row[0], row[1])
            ref = row[2].zfill(3)
            code_parent = create_model_code(row[0], ref)
            if not code_parent in models:
                code_parent = code_parent + 'A'
                if not code_parent in models:
                    code_parent = ''
            if code in models:
                return None
            models.add(code)
            return {
                "id": func_index(code, model_name),
                "code": code,
                "category_code": row[0],
                "parent_model_code": code_parent,
                "drawing": row[3],
                "quotation": row[4],
            }
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        print(f"[INFO] {len(models)} processed.")

    # Ornement Category
    if everything or "category" in sys.argv:
        model_name="pdp.product.category"
        csv_name = "OrnCatagories.csv"
        fieldnames = ["id", "code", "name", "waste"]
        def row_to_dict(row):
            return {
                "id": func_index(row[0], model_name),
                "code": row[0],
                "name" : row[1],
                "waste": float(row[3]),
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        
        
    # Matching
    if everything or "matching" in sys.argv:
        print("[WARNING] Be sure to have also import model to create models set")
        model_name="pdp.product.model.matching"
        csv_name = "MatchingModels.csv"
        fieldnames = ["id", "model_code_one", "model_code_two"]
        def row_to_dict(row):
            code_one = create_model_code(row[0], row[1])
            code_two = create_model_code(row[2], row[3])
            if not code_one in models or not code_two in models:
                return
            return {
                "id": func_index(f"{code_one}_{code_two}", model_name),
                "model_code_one": code_one,
                "model_code_two" : code_two,
            }
               
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    # Product
    if everything or "product" in sys.argv:
        
        def case_management(row):
            cases = {
                "MOP,HS,2.7", "CITA,2A,3A"
            }
            row_str = ','.join(row)
            for case in cases:
                if case in row_str:
                    rect_case = case.replace(",", "+")
                    row_str = row_str.replace(case, rect_case)
                    return row_str.split(",")
            return row
        
        model_name="pdp.product"
        csv_name = "Products.csv"
        actual_fields = ["code", "category", "model_code", "stones", "metal", "active", "creation_datetime", "remark", "prod_category", "in_collection", "orn_id_num"]
        fieldnames = ["id", "code", "category_code", "model_code", "product_stone_code", "stone_type", "metal_code", "create_date", "active", "in_collection", "remark"]
        
        def row_to_dict(row):
            row = case_management(row)
            if len(row[1]) > 2:
                stones=row[1].split("/")[0]
                old = f"{row[0][-1]},{stones}"
                new = f"{row[0][-1]}+{stones}"
                row_str = ','.join(row)
                row_str = row_str.replace(old, new)
                row = row_str.split(",")
                print(f"[INFO] Rectif {old} -> {new} in {row[0]}")
                print(f"{row_str}")
            code = create_model_code(row[1], row[2])
            stone_code = code.split["/"][0]
            return {
                "id":func_index(row[0], model_name),
                "code": row[0],
                "category_code"         : row[1],
                "model_code"            : code,
                "product_stone_code"    : stone_code, 
                "stone_type"            : safe_str(row[3]),
                "metal_code"            : safe_str(row[4]),
                "active"                : safe_str(row[5]),
                "create_date"           : safe_str(row[6]),
                "remark"                : safe_str(row[7]),
                "in_collection"         : safe_str(row[9])
            }
            
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
        
    # Product Parts
    if everything or "part" in sys.argv:
        model_name = "pdp.product.part"
        csv_name = "ProductParts.csv"
        fieldnames = ["id", "product_code", "part_code", "quantity"]
        
        def row_to_dict(row):
            if len(row) > 3:
                row[0] = f"{row[0]}+{row[1]}"
                for i in range(1, len(row)-1):
                    row[i] = row[i+1]
                del row[-1]
                return row_to_dict(row)
            
            if row[1] in {'', None}:
                return
            
            
            return {
                "id": func_index(f"{row[0]}_{row[1]}", model_name),
                "product_code": row[0],
                "part_code": row[1], 
                "quantity": int(row[2])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)


    if everything or "stone" in sys.argv:
        # B ,014B ,AQ+BT+R.MO+CHA,AQ   ,20,OVCAB,10X8,ML   ,1,.0000,.00,,US,,,,TRCAB,7X7/,1.4000,A1

        model_name = "pdp.product.stone"
        csv_name = "ModelStone.csv"
        actual_fields = [
            #0
            "cat_id", "orn_id", "stones", "stone_type", "stone_setting_code", 
            #5 
            "shape_code", "size", "shade_code", "pieces", "weight",
            #10
            "stone_unit_cost", "stone_cost", "stonecost_currency", "setting_unit_cost", "setting_cost", "setting_cost_currency",
            #16
            "shape_code_2", "size_2", "shade_2", "weight_2", "line_num" 
        ]
        fieldnames = [
            "id", "product_code", "model_code", "model_stones", "stone_code", "pieces", "weight", "shape_code", "shade_code", "size" 
        ]
        
        def row_to_dict(row):
            if len(row) < 8:
                print(f"[WARNING] This row was not imported : {'|'.join(row)}")
                return
            model_code = create_model_code(row[0], row[1])
            product_code = create_product_code(row[0], row[1], row[2])
            stone_code = create_stone_code(row[3], row[7], row[5], row[6])
            try:
                row[8] = int(row[8])
                row[9] = float(row[9])
            except:
                if len(row) > 20:
                    row[2] = f"{row[2]}+{row[3]}"
                    for i in range(3, len(row)-1):
                        row[i] = row[i+1]
                    del row[-1]
                    return row_to_dict(row)
                print(f"ERROR: {','.join(row)}")
                return 
            return {
                "id": func_index(f"{product_code}_{stone_code}", model_name),
                "product_code": product_code,
                "model_code": model_code,
                "model_stones": row[2], 
                "pieces": int(row[8]),
                "stone_code": stone_code,
                "weight": float(row[9]), 
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)

    
    # Model Metal
    if everything or "metal" in sys.argv:
        model_name="pdp.product.model.metal"
        csv_name="ModelMetal.csv"
        fieldnames=["id", "model_code", "metal_version", "metal_code", "purity", "weight"]
        
        def row_to_dict(row):
            model_code = create_model_code(row[0], row[1])
            if row[2] in {'', '\x00', None}:
                if row[3] in {'', '\x00', None}:
                    row[3] = 'W'
                row[2] = row[3]
            elif row[3] in {'', '\x00', None}:
                row[3] = row[2]
            row[3] = re.sub(r'[0-9 ]','',row[3])
            if len(models) > 0 and not model_code in models:
                print(f"[WARNING] {model_code} NOT IN MODELS")
                
            row[4] = row[4].replace(" ", "").upper()
            return {
                "id": func_index(f"{model_code}{row[2]}_{row[3]}_{row[4]}", model_name),
                "model_code": model_code,
                "metal_version": row[2],
                "metal_code": row[3],
                "purity": row[4], 
                "weight": safe_float(row[5])
            }
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
