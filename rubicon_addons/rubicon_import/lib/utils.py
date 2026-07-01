import logging
import os
import time
from contextlib import contextmanager

_logger = logging.getLogger(__name__)

def is_empty(value):
    """Treats as empty: '', None, '\\x00'."""
    return value in {'', None, '\x00'}

def csv_abs_path(module_file, rel_path):
    """Absolute path of a CSV from this Odoo package."""
    module_dir = os.path.dirname(module_file)
    return os.path.join(module_dir, '../..', rel_path)

@contextmanager
def chrono():
    t0 = time.time()
    yield
    dt = time.time() - t0
    _logger.info("Time elapsed: %.2fs", dt)
