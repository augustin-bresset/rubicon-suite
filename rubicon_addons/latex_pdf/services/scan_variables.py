import jinja2
from jinja2 import nodes, meta

def scan_variables(template_str):
    """
    Scan a latex template and returns its parameters.
    RETURN
    ------
        {
            "variable_a" : None,
            "variable_b" : None,
            ...
            
            "iterator_a" : [obj.field_a, obj.field_b, obj.field_c],
            ...
        }
    """
    
    env = jinja2.Environment(
        block_start_string='\\BLOCK{',
        block_end_string='}',
        variable_start_string='\\VAR{',
        variable_end_string='}',
        autoescape=False
    )
    parsed_content = env.parse(template_str)

    all_variables = meta.find_undeclared_variables(parsed_content)
    tables = {}

    def walk(node, loop_var_map=None):
        if loop_var_map is None:
            loop_var_map = {}

        if isinstance(node, nodes.For):
            loop_target = node.target.name
            loop_iter = node.iter.name
            loop_var_map[loop_target] = loop_iter
            tables.setdefault(loop_iter, set())

            for child in node.body:
                walk(child, loop_var_map.copy())

        elif isinstance(node, nodes.Getattr):
            if isinstance(node.node, nodes.Name):
                var_name = node.node.name
                attr_name = node.attr
                if var_name in loop_var_map:
                    iter_name = loop_var_map[var_name]
                    tables.setdefault(iter_name, set()).add(attr_name)

        for field_name in node.fields:
            field = getattr(node, field_name)
            if isinstance(field, list):
                for item in field:
                    if isinstance(item, nodes.Node):
                        walk(item, loop_var_map.copy())
            elif isinstance(field, nodes.Node):
                walk(field, loop_var_map.copy())

    walk(parsed_content)
    out = dict()
    for var in all_variables:
        out[var] = None
    for key, value in tables.items():
        out[key] = list(value)
    return out        
    
if __name__ == "__main__":
    latex_template = r"""
    \BLOCK{ for row in items }
    \VAR{row.name} & \VAR{row.description} & \VAR{row.quantity} \\
    \BLOCK{ endfor }
    

    Client: \VAR{client_name}
    """

    variables = scan_variables(latex_template)
    print(variables)

    # variables, tables = scan_variables(latex_template)

    # print("Variables simples :", variables)
    # print("Tables détectées :", tables)
    env = jinja2.Environment(
        block_start_string='\\BLOCK{',
        block_end_string='}',
        variable_start_string='\\VAR{',
        variable_end_string='}',
        autoescape=False
    )
    """
    Template(body=[
        Output(nodes=[TemplateData(data='\n    ')]), 
        For(target=Name(name='row', ctx='store'), 
            iter=Name(name='items', ctx='load'), 
            body=[Output(nodes=[TemplateData(data='\n    '), 
                                Getattr(node=Name(name='row', ctx='load'), attr='name', ctx='load'), 
                                TemplateData(data=' & '), 
                                Getattr(node=Name(name='row', ctx='load'), attr='description', ctx='load'), 
                                TemplateData(data=' & '), 
                                Getattr(node=Name(name='row', ctx='load'), attr='quantity', ctx='load'), 
                                TemplateData(data=' \\\\\n    ')
            ])],
            else_=[], 
            test=None, 
            recursive=False), 
        Output(nodes=[TemplateData(data='\n\n    Client: '), 
                      Name(name='client_name', ctx='load'), 
                      TemplateData(data='\n    ')])])

    """
    
    