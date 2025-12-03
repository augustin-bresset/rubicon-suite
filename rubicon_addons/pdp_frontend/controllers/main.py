from odoo import http
from odoo.http import request


class PDPFrontendController(http.Controller):
    @http.route("/pdp", type="http", auth="user", website=True)
    def pdp_home(self, **kwargs):
        """Serve the PDP frontend preview page."""
        return request.render("pdp_frontend.pdp_frontend_page", {})