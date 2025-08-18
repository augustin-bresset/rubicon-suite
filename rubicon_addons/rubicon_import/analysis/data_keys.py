import os
import csv
import types


root_folder = os.path.join(os.path.dirname(__file__), '../../..')
# Folders
backup_folder = os.path.join(root_folder, 'data', 'backup_pdp')
data_folder = os.path.join(root_folder, 'data', 'odoo')


modules_folder = os.path.join(root_folder, 'rubicon_addons')
pdp_data_folders = [
    os.path.join(modules_folder, module, 'data')
    for module in os.listdir(modules_folder) if module.startswith('pdp_')
]

logs = {
    
}

for pdp_data_folder in pdp_data_folders:
    module_name = pdp_data_folder.split('/')[-2]
    if not os.path.isdir(pdp_data_folder):
        continue
    for file_name in os.listdir(pdp_data_folder):
        file_path = os.path.join(pdp_data_folder, file_name)
        records_xml_id = set()
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            headers = rows[0][1:]  # on ignore la première colonne (XML ID)
            for row in rows[1:]:
                xml_id = row[0]
                if xml_id in records_xml_id:
                    if logs.get(file_name) is None:
                        logs[file_name] = []
                    logs[file_name].append(xml_id)
                else:
                    records_xml_id.add(xml_id)
                    
print(f"[INFO] RESULTS XML ID:")
if len(logs) > 0:
    print(f"Files with problems")
    for k, v in logs.items():
        if len(v) > 0:
            print(f"- {k} : {len(v)} errors")
            print("\n==>".join(v[:5]))
else:
    print(f"[INFO] No Issue")
    

logs = {}

for pdp_data_folder in pdp_data_folders:
    module_name = pdp_data_folder.split('/')[-2]
    if not os.path.isdir(pdp_data_folder):
        continue
    for file_name in os.listdir(pdp_data_folder):
        file_path = os.path.join(pdp_data_folder, file_name)
        records_key = set()
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            headers = rows[0][1:]  # on ignore la première colonne (XML ID)
            for row in rows[1:]:
                key = "_".join(row[1:])
                if key in records_key:
                    if logs.get(file_name) is None:
                        logs[file_name] = []
                    logs[file_name].append(key)
                else:
                    records_key.add(key)

print(f"[INFO] RESULTS VALUES:")
if len(logs) > 0:
    print(f"Files with problems")
    for k, v in logs.items():
        if len(v) > 0:
            print(f"- {k} : {len(v)} errors")
            print("\n==>".join(v[:5]))
else:
    print(f"[INFO] No Issue")