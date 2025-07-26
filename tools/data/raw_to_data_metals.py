import os
import sys
import csv
import sys

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
                if index_auto:
                    out["id"] = func_index(str(i), model_name)
                writer.writerow(out)
    print(f"Generated {dest_name}")


        

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
        