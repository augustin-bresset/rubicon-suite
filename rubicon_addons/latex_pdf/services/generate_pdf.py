import subprocess
import jinja2
import tempfile

# Maximum wall-clock time for a single pdflatex run. A crafted template
# (e.g. \def\x{\x}\x) can loop forever even with -interaction=nonstopmode,
# which would otherwise pin an Odoo worker indefinitely.
PDFLATEX_TIMEOUT_SECONDS = 15

# LaTeX special characters that must be neutralised in interpolated values so
# an attacker-supplied variable cannot inject commands such as \input{/etc/passwd}
# or \lstinputlisting{...} (arbitrary file read) into the compiled document.
_LATEX_SPECIALS = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
}


def _latex_escape(value):
    """Recursively escape LaTeX-special characters in interpolated values.

    Strings are escaped; dicts/lists are walked so nested structures (the
    documented `iterable` case) are covered too. Other scalars pass through.
    """
    if isinstance(value, str):
        return ''.join(_LATEX_SPECIALS.get(ch, ch) for ch in value)
    if isinstance(value, dict):
        return {key: _latex_escape(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_latex_escape(item) for item in value]
    return value


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
    safe_variables = {key: _latex_escape(val) for key, val in variables.items()}
    latex_filled = template.render(**safe_variables)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = f"{tmpdir}/output.tex"
        pdf_path = f"{tmpdir}/output.pdf"

        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_filled)

        # -no-shell-escape blocks \write18 command execution.
        # cwd/-output-directory are confined to the temp dir.
        subprocess.run(
            ['pdflatex', '-no-shell-escape', '-interaction=nonstopmode',
             '-output-directory', tmpdir, tex_path],
            check=True,
            timeout=PDFLATEX_TIMEOUT_SECONDS,
            cwd=tmpdir,
        )

        with open(pdf_path, 'rb') as pdf_file:
            return pdf_file.read()
