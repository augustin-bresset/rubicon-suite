import os
import time
from contextlib import contextmanager

def is_empty(value):
    """Considère vide: '', None, '\\x00'."""
    return value in {'', None, '\x00'}

def csv_abs_path(module_file, rel_path):
    """Chemin absolu d'un CSV depuis ce package Odoo."""
    module_dir = os.path.dirname(module_file)
    return os.path.join(module_dir, '../..', rel_path)

@contextmanager
def chrono():
    t0 = time.time()
    yield
    dt = time.time() - t0
    print(f"[INFO] Time elapsed: {dt:.2f}s")
