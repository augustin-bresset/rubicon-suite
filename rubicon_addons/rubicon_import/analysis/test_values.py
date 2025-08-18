# Revised script: scans pdp_* modules' data/ folders and
# 1) detects duplicate XML IDs (first CSV column)
# 2) detects duplicates ONLY on columns that have a configured uniqueness constraint
#
# Configure per-file (or pattern) unique constraints in UNIQUE_MAP below.
# Supports exact file name or fnmatch-style glob patterns.
#
# Save as check_pdp_csv_uniques.py
import re
import os
import csv
import fnmatch
from collections import defaultdict, Counter

def unique_columns_from_clause(clause):
    """
    Extrait les noms de colonnes d'une clause UNIQUE(...) en tuple.
    """
    m = re.search(r'unique\s*\((.*?)\)', clause, re.IGNORECASE)
    if not m:
        return ()
    cols_str = m.group(1)
    cols = [c.strip().strip('"').strip("'") for c in cols_str.split(',')]
    return tuple(cols)

def test_module_model(env, module_name, model_name, 
                      path_modules=os.path.join(os.path.dirname(__file__), "../..")
                      ):
    print(os.listdir(os.path.join(os.path.dirname(__file__), "../..")))
    data_folder = os.path.join(path_modules, module_name, 'data')
    ModelClass = env[model_name].__class__
    logs = []
    if hasattr(ModelClass, "_sql_constraints"):
        sql_constraints = ModelClass._sql_constraints
        file_path = os.path.join(data_folder, model_name+'.csv')
        for constraint in sql_constraints:
            if not "uniq" in constraint[0]:
                continue
            uniq_fiels = unique_columns_from_clause(constraint[1])
            
            records_key = set()
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)

                headers = rows[0][1:]  # on ignore la première colonne (XML ID)
                for row in rows[1:]:
                    key = []
                    for header, value in zip(headers, row[1:]):
                        if header in uniq_fiels:
                            key.append(value)
                    key = tuple(key)
                    if key in records_key:
                        logs.append(key)
                    else:
                        records_key.add(key)
            if len(logs) > 0:
                print(f"For constraint : {constraint}")
                print(f"There is {len(logs)} collisions")
                print(logs[:3])

                        