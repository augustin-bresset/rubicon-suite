import subprocess
import jinja2
import tempfile

def generate_pdf_from_latex(template_str, variables):
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

if __name__ == "__main__":
    latex_template = r"""
    \documentclass{article}
    \usepackage{longtable}
    \title{Test}
    \begin{document}

    \begin{longtable}{|l|l|r|}
    \hline
    Item & Description & Quantity \\
    \hline
    \BLOCK{ for row in items }
    \VAR{row.name} & \VAR{row.description} & \VAR{row.quantity} \\
    \hline
    \BLOCK{ endfor }
    \end{longtable}

    \end{document}
    """
    data = {
        'items': [
            {'name': 'Ring A', 'description': 'Gold Ring', 'quantity': 1},
            {'name': 'Bracelet B', 'description': 'Silver Bracelet', 'quantity': 2},
            {'name': 'Pendant C', 'description': 'Diamond Pendant', 'quantity': 3},
        ]
    }
    pdf_content = generate_pdf_from_latex(latex_template, data)

    with open('generated_table.pdf', 'wb') as f:
        f.write(pdf_content)

    print("PDF généré : generated_table.pdf")
