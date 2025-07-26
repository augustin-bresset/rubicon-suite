import subprocess
import jinja2
import tempfile

def generate_pdf_from_latex(template_str, variables):
    """
    
    PARAMETERS
    ----------
     template_str : str
     variables : dict
     
        template_str = ""\\
        variables = {
            'var_a' :  42,
            'iterable' : [
                {'field_one': val1, 'field_two': val2},
                 ...
            ]
        }
    """
    env = jinja2.Environment(
        block_start_string='\\BLOCK{',
        block_end_string='}',
        variable_start_string='\\VAR{',
        variable_end_string='}',
        autoescape=False
    )
    template = env.from_string(template_str)
    latex_filled = template.render(**variables)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = f"{tmpdir}/output.tex"
        pdf_path = f"{tmpdir}/output.pdf"

        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_filled)

        subprocess.run(['pdflatex', '-interaction=nonstopmode', '-output-directory', tmpdir, tex_path], check=True)

        with open(pdf_path, 'rb') as pdf_file:
            return pdf_file.read()