import os
import sys
import csv

""" Source file head 3 :
1,All,,.000,US,0,0 
D,Diamond,,.000,US,0,D 
H,Hard Stone,,.000,US,1,DI
P,Precious Stone,,.000,US,1,S 
R,Pearl,,.000,US,0,DI
S,Semi Precious Stone,,.000,US,1,S 
"""
header = ("code", "name", "name2", "f1", "f2", "f3")

root_folder = os.path.join(os.path.dirname(__file__), 'rubicon-suite')
# Folders
backup_folder = os.path.join('data', 'backup_pdp')
data_folder = os.path.join('data', 'odoo')

def main():
    file_name = os.path.join(backup_folder, "StoneCategories.csv")
    
    dest_name = os.path.join(data_folder, "pdp.stone.category.csv")

    with open(file_name, newline='', encoding='utf-8') as src_file:
        reader = csv.reader(src_file)
        # Prepare header: external id + model_fields
        
        with open(dest_name, 'w', newline="", encoding='utf-8') as dst_file:
            writer = csv.DictWriter(dst_file, fieldnames=("id", "code", "name"))
            writer.writeheader()
            
            for row in reader:
                out = {
                    "id" : row[0].replace(" ", "_"),
                    "code" : row[0],
                    "name" : row[1],
                }
                writer.writerow(out)
    print(f"Generated {dest_name}")


        

if __name__ == '__main__':
    # Examples for pdp module
    main()
    