import os
import csv
import types

from rubicon_import.tools.standard import func_index

root_folder = os.path.join(os.path.dirname(__file__), '../../..')
# Folders
backup_folder = os.path.join(root_folder, 'data', 'backup_pdp')
data_folder = os.path.join(root_folder, 'data', 'odoo')



def fixing_row(row):
    while len(row) > 4:
        row[0] = f"{row[0]}+{row[1]}"
        for i in range(1, len(row)-1):
            row[i] = row[i+1]
        del row[-1]
        
def analysis_solder_recutting(file_name):
    ...