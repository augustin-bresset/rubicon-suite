import csv
import logging

_logger = logging.getLogger(__name__)


def read_csv_as_dicts(path):
    """
    Returns (headers, rows) where rows = [ {header: value}, ... ].
    If the file is empty: ([], []).
    """
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        _logger.warning("CSV file is empty: %s", path)
        return [], []
    headers = rows[0]
    dict_rows = [dict(zip(headers, r)) for r in rows[1:]]
    return headers, dict_rows
