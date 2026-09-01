import werkzeug.exceptions

from odoo import http
from odoo.http import request


class PcsBarcodeController(http.Controller):
    """Code 39 rendering for the stock cards.

    Odoo's /report/barcode cannot disable the mod-43 check character that
    reportlab appends to Standard39 by default; a plain Code 39 scanner
    would then read one extra character and the scan would not match.
    This route renders Standard39 with checksum=0, like the legacy cards.
    """

    # Upper bounds so an unauthenticated caller cannot force a huge allocation
    # (e.g. width=99999999) and exhaust worker memory.
    MAX_WIDTH = 2000
    MAX_HEIGHT = 500

    @http.route('/pcs_document/barcode39', type='http', auth='public')
    def barcode39(self, value='', width=600, height=100, **kwargs):
        try:
            from reportlab.graphics.barcode import createBarcodeDrawing
            safe_width = max(1, min(int(width), self.MAX_WIDTH))
            safe_height = max(1, min(int(height), self.MAX_HEIGHT))
            drawing = createBarcodeDrawing(
                'Standard39', value=value, format='png',
                width=safe_width, height=safe_height,
                checksum=0, quiet=True, humanReadable=False)
            png = drawing.asString('png')
        except (ValueError, AttributeError):
            raise werkzeug.exceptions.NotFound(
                'Cannot render this value as a Code 39 barcode.')
        return request.make_response(
            png, headers=[('Content-Type', 'image/png')])
