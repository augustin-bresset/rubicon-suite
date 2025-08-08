import os
import csv
import types
import time
from rubicon_import.tools.standard import func_index

root_folder = os.path.join(os.path.dirname(__file__), '../../..')
# Folders
backup_folder = os.path.join(root_folder, 'data', 'backup_pdp')
data_folder = os.path.join(root_folder, 'data', 'odoo')

def raw_to_data(
    model_name, 
    csv_name, 
    fieldnames, 
    row_to_dict, 
    index_auto=False,
    xml_idx=True,
    verbose=True
    ):
    t0 = time.time()
    logs = {"created": 0, "skipped": 0, "total": 0}

    dest_name = os.path.join(data_folder, f"{model_name}.csv")
    
    file_name = os.path.join(backup_folder, csv_name)

    if index_auto and not xml_idx:
        print(f'[WARN] Know what you want ! an auto index but no index... weirdooo, so auto index for YOU ! xml_idx is True')
        xml_idx = True
    
    if fieldnames[0] != "id":
        if xml_idx:
            fieldnames = ["id"] + fieldnames
    elif not xml_idx:
        del fieldnames[0]

    with open(file_name, newline='', encoding='utf-8') as src_file:
        reader = csv.reader(src_file)
        # Prepare header: external id + model_fields
        
        with open(dest_name, 'w', newline="", encoding='utf-8') as dst_file:
            writer = csv.DictWriter(dst_file, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, row in enumerate(reader):
                logs["total"] +=1
                out = row_to_dict(row)
                
                if isinstance(out, types.GeneratorType):
                    for d in out:
                        if d.get("id") and not xml_idx:
                            del d["id"]
                        if out is not None:
                            if index_auto:
                                d["id"] = func_index(str(i), model_name)
                            writer.writerow(d)
                            logs["created"]+=1
                        else:
                            logs["skipped"]+=1
                
                elif out is not None:  
                    if out.get("id") and not xml_idx:
                        del out["id"]                  
                    if index_auto:
                        out["id"] = func_index(str(i), model_name)
                    writer.writerow(out)
                    logs["created"]+=1
                else:
                    logs["skipped"]+=1

    print(f"Generated {dest_name}")
    duration = time.time() - t0
    if verbose:
        print(f"Import for {model_name}:")
        for k,v in logs.items():
           print(f"  => {k.title()}    : {v}")            
        print(f"  => Time elapsed  : {duration:.2f} seconds")

    return logs
