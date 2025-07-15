"""
This script create a `data` directory in the pdp module of odoo.
This folder will contains multiple csv files containings the data that will be used by pdp.
Those data come from raw data imported from a backup and transform into csv files.
"""
import os
import sys
import csv

# Folders
backup_folder = os.path.join(os.path.dirname(__file__), 'data', 'backup_pdp')
data_folder = os.path.join(os.path.dirname(__file__), 'data', 'odoo')

# Ensure data folder exists
os.makedirs(data_folder, exist_ok=True)

# Module namespace for external IDs
def make_external_id(module_prefix, model_name, key_value):
    # sanitize key_value
    key = str(key_value).strip().replace(' ', '_').lower()
    return f"{module_prefix}.{model_name}_{key}"


def csv_backup_to_data(file_name, module_prefix, model_name, model_fields, id_field):
    """
    Convert a backup CSV into an Odoo data CSV for model import.

    :param file_name: backup CSV name under backup_folder
    :param module_prefix: prefix for external IDs (e.g. 'pdp' or 'rubicon')
    :param model_name: name of the Odoo model (e.g. 'item', 'stone')
    :param model_fields: list of field names to include in output (must exist in backup)
    :param id_field: name of the field from backup used to generate external ID
    """
    src_path = os.path.join(backup_folder, file_name)
    dest_name = f"{module_prefix}.{model_name}.csv"
    dest_path = os.path.join(data_folder, dest_name)

    with open(src_path, newline='', encoding='utf-8') as src_file:
        reader = csv.DictReader(src_file)
        # Prepare header: external id + model_fields
        header = ['id'] + model_fields
        with open(dest_path, 'w', newline='', encoding='utf-8') as dst_file:
            writer = csv.DictWriter(dst_file, fieldnames=header)
            writer.writeheader()
            for row in reader:
                key_val = row.get(id_field)
                if not key_val:
                    continue  # skip if no identifier
                ext_id = make_external_id(module_prefix, model_name, key_val)
                out = {'id': ext_id}
                for f in model_fields:
                    out[f] = row.get(f, '')
                writer.writerow(out)
    print(f"Generated {dest_path}")

def backup_to_data_stone_size():
    file_name = "StoneSizes.csv"
    src_path = os.path.join(backup_folder, file_name)
    model_fields = ['size', 'description']
    with open(src_path, newline='', encoding='utf-8') as src_file:
        reader = csv.reader(src_file)
        header = ['id'] + model_fields
        
        with open(des)
        

if __name__ == '__main__':
    # Examples for pdp module
    
    csv_backup_to_data(
        file_name='StoneSizes.csv',
        module_prefix='pdp',
        model_name='stone',
        model_fields=[
            'stone_type_id', 'shape_id', 'shade_id', 'size_id',
            'weight', 'cost', 'currency_id', 'item_id'
        ],
        id_field='id'  # assuming backup has its own numeric id
    )

    csv_backup_to_data(
        file_name="stones_backup.csv",
        module_prefix=
    )