import json
import base64
from odoo import models, fields, api


from .services.scan_variables import scan_variables
from .services.generate_pdf import generate_pdf_from_latex


class PdfTemplate(models.Model):
    _name = 'pdfg.template'
    _description = 'Template of the PDF'
    _rec_name = "name"    

    name = fields.Char(
        string='Template Name', 
        required=True)

    latex_template = fields.Text(
        string='Latex Template', 
        required=True)

    variables = fields.Json(
        string="Variables Structure",
        readonly=True)
    
    preview_pdf = fields.Binary(
        string='Template Preview'
    )

    def update_variables_info(self):
        for record in self:
            variables_dict = scan_variables(record.latex_template)
            record.variables = variables_dict

    def generate_preview_pdf(self):
        for record in self:
            pdf_content = generate_pdf_from_latex(record.latex_template, {key: "Example" for key in (record.variables or {}).keys()})
            record.preview_pdf = base64.b64encode(pdf_content)