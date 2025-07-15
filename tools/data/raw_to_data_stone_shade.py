import os
import sys
import csv

""" Source file head 3 :
0    ,None,
1    ,All,
2    ,2 Good,
3    ,3 Medium,
A    ,A Light Color,
AA   ,AA Medium Color,
AAA  ,AAA Dark Color,
AAAA ,AAAA Darker Color,
"""
header = ("code", "shade", "")

root_folder = os.path.join(os.path.dirname(__file__), 'rubicon-suite')
# Folders
backup_folder = os.path.join('data', 'backup_pdp')
data_folder = os.path.join('data', 'odoo')

def main():
    file_name = os.path.join(backup_folder, "StoneShades.csv")
    
    dest_name = os.path.join(data_folder, "pdp.stone.shade.csv")

    with open(file_name, newline='', encoding='utf-8') as src_file:
        reader = csv.reader(src_file)
        # Prepare header: external id + model_fields
        
        with open(dest_name, 'w', newline="", encoding='utf-8') as dst_file:
            writer = csv.DictWriter(dst_file, fieldnames=("id", "code", "shade"))
            writer.writeheader()
            
            for row in reader:
                out = {
                    "id" : row[0].replace(" ", "_"),
                    "code" : row[0],
                    "shade" : row[1],
                    }
                writer.writerow(out)
    print(f"Generated {dest_name}")


        

if __name__ == '__main__':
    # Examples for pdp module
    main()
    