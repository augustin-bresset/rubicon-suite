
def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def safe_str(val):
    if val in {'\x00', None}:
        return ''
    return val
    