

def func_index(code:str, model_name:str):
    return f"{model_name}.{code.replace(" ", "_")}"

def rev_func_index(id):
    id_split = id.split(".")
    model_name, code = ".".join(id_split[:-1]), id_split.replace("_", " ")
    return model_name, code
    

    