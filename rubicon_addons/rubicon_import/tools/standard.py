import re


def func_index(code:str, model_name:str):
    model_name = model_name.split(".")[-1]
    code = re.sub(r"[ .-/+-]", "_", code)
    return f"{model_name}_{code}"


def create_model_code(category, code):
    model_code_ = ''.join((category, code.zfill(3)))
    model_code_ = re.sub(r'[ ]', '', model_code_).upper()
    
    return model_code_

def create_product_composition_code(category, code, stones):
    return f"{category.rstrip(' ')}{code.zfill(3).rstrip(' ')}-{stones}"    
    return re.sub(r'[ ]', '', product_code)



def mapping_currency(currency, default="USD"):
    if currency == '':
        return default
    currency = currency.upper()
    currency = currency.strip()
    map_ = {
        "US" : "USD",
        "TH" : "THB",
    }    
    new_curr = map_.get(currency) 
    return  new_curr if new_curr is not None else currency 


def strip_code_space(code, upper=True):
    """Strip space but not the one used.
    :example::
     > code_space("AA   ")
     >>> "AA"
     > code_space("AA B ")
     >>> "AA B"
    """
    code = code.replace('  ', '') # Del double space
    if code == '':
        return ''
    if code[-1] == ' ':
        return code[:-1]
    return code.upper()

def create_stone_code(stone_type, stone_shade, stone_shape, size):
    stone_type = stone_type.rstrip(' ')
    stone_shape = stone_shape.rstrip(' ')
    stone_shade = stone_shade.rstrip(' ')
    size = size.rstrip(' ')    
    
    if stone_shade == '1':
        stone_shade = ''
    if stone_shape == '1':
        stone_shape = ''
    
    stone_code = [f"{stone_type}{stone_shade}"]
    if stone_shape:
        stone_code.append(stone_shape)
    if size:
        stone_code.append(size)
        
    return '-'.join(stone_code)

def size_field(size):
    if len(size) == 0 or re.sub(r"[0.]", "", size) == '':
        return ''

    try:
        size = str(float(size))
    except:
        pass
    
    size = size.upper()
    if size[0] == '.':
        size = '0'+size
    
    return size



