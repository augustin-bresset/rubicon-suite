import os
import sys
import csv

""" Source file head 3 :
0    ,None,, ,
1    ,All,,1,
ABA  ,Abalone,,H,1.00
"""
header = ("code", "name", "", "category_code", "density_ref")

root_folder = os.path.join(os.path.dirname(__file__), 'rubicon-suite')
# Folders
backup_folder = os.path.join('data', 'backup_pdp')
data_folder = os.path.join('data', 'odoo')

def main():
    file_name = os.path.join(backup_folder, "StoneTypes.csv")
    
    dest_name = os.path.join(data_folder, "pdp.stone.type.csv")

    with open(file_name, newline='', encoding='utf-8') as src_file:
        reader = csv.reader(src_file)
        # Prepare header: external id + model_fields
        
        with open(dest_name, 'w', newline="", encoding='utf-8') as dst_file:
            writer = csv.DictWriter(dst_file, fieldnames=("id", "code", "name", "category_code", "density"))
            writer.writeheader()
            
            for row in reader:
                if row[4] == "": row[4] = 0.0
                density = float(row[4]) * 2.65
                out = {
                    "id" : row[0].replace(" ", "_"),
                    "code" : row[0],
                    "name" : row[1],
                    "category_code" : row[3],
                    "density" : density
                }
                writer.writerow(out)
    print(f"Generated {dest_name}")


        

if __name__ == '__main__':
    # Examples for pdp module
    main()
    