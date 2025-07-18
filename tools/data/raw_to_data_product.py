import os
import sys
import csv
import sys
import re

def func_index(code:str, model_name:str):
    model_name = model_name.split(".")[-1]
    code = code.replace(".", "_")
    code = code.replace("-", "_")
    code = code.replace(" ", "_")
    code = code.replace("/", "_")
    return f"{model_name}_{code}"


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




def model_code(category, code):
    model_code_ = ''.join((category,code))
    model_code_ = re.sub(r'[ Aa]', '', model_code_).upper()
    return model_code_

if __name__ == '__main__':
    # Examples for pdp module
    everything = True
    if len(sys.argv) > 1:
        everything = False
        print(f"Begin generation for {sys.argv[1:]}")
    
    models = set()
    # Model
    # B ,014B ,14,B014B-N-2,
    if everything or "model" in sys.argv:
        model_name="pdp.product.model"
        csv_name = "Models.csv"
        fieldnames = ["id", "code", "category_code", "parent_model_code", "drawing", "quotation"]
        def row_to_dict(row):
            code = model_code(row[0], row[1])
            ref = row[2].zfill(3)
            code_parent = model_code(row[0], ref)
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
    print(len(models))
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
        model_name="pdp.product.model.matching"
        csv_name = "MatchingModels.csv"
        fieldnames = ["id", "model_code_one", "model_code_two"]
        def row_to_dict(row):
            code_one = model_code(row[0], row[1])
            code_two = model_code(row[2], row[3])
            if not code_one in models:
                print(f"Model {code_one} not found in Model table")
                return
            if not code_two in models:
                print(f"Model {code_two} not found in Model table")
                return
            
            return {
                "id": func_index(f"{code_one}_{code_two}", model_name),
                "model_code_one": code_one,
                "model_code_two" : code_two,
            }
               
        raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    