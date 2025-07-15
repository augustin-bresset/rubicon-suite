import os
import sys
import csv


def func_index(code:str, model_name:str):
    return f"{model_name}.{code.replace(" ", "_")}"


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



def raw_to_data(model_name, csv_name, fieldnames, row_to_dict):
    
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
            
            for row in reader:
                out = row_to_dict(row)
                writer.writerow(out)
    print(f"Generated {dest_name}")


        

if __name__ == '__main__':
    # Examples for pdp module
    
    # Type
    model_name = "pdp.stone.type"
    csv_name = "StoneTypes.csv"
    fieldnames = ["id", "code", "name", "density", "category_code"]
    def row_to_dict_type(row):
        if row[4] == "": row[4] = 0.0
        density = float(row[4]) * 2.65
        return {
            "id" : func_index(row[0], model_name),
            "code" : row[0],
            "name" : row[1],
            "density" : density,
            "category_code" : row[3],
            # "category_id" : func_index(row[3], "pdp.stone.category"),
        }
    
    raw_to_data(model_name, csv_name, fieldnames, row_to_dict_type)
    
    # Category
    model_name = "pdp.stone.category"
    csv_name = "StoneCategories.csv"
    fieldnames = ["id", "code", "name"]
    def row_to_dict_cat(row):
        return {
            "id" : func_index(row[0], model_name),
            "code" : row[0],
            "name" : row[1],
            }
        
    raw_to_data(model_name, csv_name, fieldnames, row_to_dict_cat)
    
    # Size
    model_name = "pdp.stone.size"
    csv_name = "StoneSizes.csv"
    fieldnames = ["size"]
    def row_to_dict(row):
        return {
            "id": func_index(row[0], model_name),
            "size": row[0]
        }
    raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    # Shade
    model_name = "pdp.stone.shade"
    csv_name = "StoneShades.csv"
    fieldnames = ["code", "shade"]
    def row_to_dict(row):
        return {
            "id": func_index(row[0], model_name),
            "code": row[0],
            "shade": row[1]
        }
    raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
    # Shape
    model_name = "pdp.stone.shape"
    csv_name = "StoneShapes.csv"
    fieldnames = ["code", "shape"]
    def row_to_dict(row):
        return {
            "id": func_index(row[0], model_name),
            "code": row[0],
            "shape": row[1]
        }
    raw_to_data(model_name, csv_name, fieldnames, row_to_dict)
    
