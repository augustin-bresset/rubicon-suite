import csv

def read_csv_as_dicts(path):
    """
    Retourne (headers, rows) où rows = [ {header: value}, ... ].
    Si le fichier est vide: ([], []).
    """
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        print("CSV file is empty.")
        return [], []
    headers = rows[0]
    dict_rows = [dict(zip(headers, r)) for r in rows[1:]]
    return headers, dict_rows
