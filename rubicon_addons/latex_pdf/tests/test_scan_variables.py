from ..services.scan_variables import scan_variables

latex_template = r"""
    \BLOCK{ for row in items }
    \VAR{row.name} & \VAR{row.description} & \VAR{row.quantity} \\
    \BLOCK{ endfor }

    Client: \VAR{client_name}
"""

variables, tables = scan_variables(latex_template)

assert variables == ['client_name', 'items']
assert tables == {'items': ['description', 'name', 'quantity']}
