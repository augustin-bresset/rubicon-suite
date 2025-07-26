from odoo import http
from odoo.http import request, route
import base64

from latex_pdf.services.generate_pdf import generate_pdf_from_latex

class PdfgController(http.Controller):
    @route(['/pdfg/api/generate'], type='json', auth='public', methods=['POST'])
    def generate_pdf(self, template_id, variables):
        template = request.env['pdfg.template'].sudo().browse(template_id)
        if not template.exists():
            return {'error': 'Template not found'}

        pdf_bytes = generate_pdf_from_latex(template.latex_template, variables)
        return {
            'pdf_base64': base64.b64encode(pdf_bytes).decode('utf-8')
        }
