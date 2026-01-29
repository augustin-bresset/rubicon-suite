import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class PdpApiController(http.Controller):
    """
    REST API Controller for PDP.
    All endpoints require authentication via JWT token.
    """

    # ==========================================================================
    # Products Endpoints
    # ==========================================================================

    @http.route('/api/v1/pdp/products/<int:product_id>', type='http', auth='none',
                methods=['GET'], cors='*', csrf=False)
    def get_product(self, product_id, **kwargs):
        """
        GET /api/v1/pdp/products/<id>
        Returns full PDP data for a product.
        Requires: product.read permission
        """
        # Authenticate via JWT
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user  # Error response

        # Check permission
        perm_error = self._check_permission(user, 'product.read')
        if perm_error:
            return perm_error

        try:
            service = request.env['pdp.api.service'].with_user(user)
            data = service.get_full_pdp(product_id)
            return self._json_response(data)
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/v1/pdp/products', type='http', auth='none',
                methods=['GET'], cors='*', csrf=False)
    def list_products(self, model_id=None, limit=100, offset=0, **kwargs):
        """
        GET /api/v1/pdp/products
        Returns list of products, optionally filtered by model.
        Requires: product.read permission
        """
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user

        # Check permission
        perm_error = self._check_permission(user, 'product.read')
        if perm_error:
            return perm_error

        try:
            domain = []
            if model_id:
                domain.append(('model_id', '=', int(model_id)))

            products = request.env['pdp.product'].with_user(user).search(
                domain, limit=int(limit), offset=int(offset)
            )

            data = {
                'products': [{
                    'id': p.id,
                    'code': p.code,
                    'name': p.name,
                    'model_id': p.model_id.id if p.model_id else None,
                    'model_code': p.model_id.code if p.model_id else '',
                } for p in products],
                'total': request.env['pdp.product'].with_user(user).search_count(domain),
            }
            return self._json_response(data)
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._json_response({'error': str(e)}, status=500)

    # ==========================================================================
    # Price Endpoints
    # ==========================================================================

    @http.route('/api/v1/pdp/products/<int:product_id>/price', type='http', auth='none',
                methods=['POST'], cors='*', csrf=False)
    def compute_price(self, product_id, **kwargs):
        """
        POST /api/v1/pdp/products/<id>/price
        Body: { "margin_id": 1, "currency_id": 2 }
        Returns computed price breakdown.
        Requires: price.compute permission
        """
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user

        # Check permission
        perm_error = self._check_permission(user, 'price.compute')
        if perm_error:
            return perm_error

        try:
            # Parse JSON body
            body = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            margin_id = body.get('margin_id')
            currency_id = body.get('currency_id')

            service = request.env['pdp.api.service'].with_user(user)
            data = service.compute_price(product_id, margin_id, currency_id)
            return self._json_response(data)
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._json_response({'error': str(e)}, status=500)

    # ==========================================================================
    # Metadata Endpoints
    # ==========================================================================

    @http.route('/api/v1/pdp/metadata', type='http', auth='none',
                methods=['GET'], cors='*', csrf=False)
    def get_metadata(self, **kwargs):
        """
        GET /api/v1/pdp/metadata
        Returns all reference data (currencies, margins, models, metals).
        """
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user

        try:
            env = request.env
            data = {
                'currencies': env['res.currency'].with_user(user).search_read(
                    [('active', '=', True)], ['id', 'name', 'symbol', 'rate']
                ),
                'margins': env['pdp.margin'].with_user(user).search_read(
                    [], ['id', 'name']
                ),
                'models': env['pdp.product.model'].with_user(user).search_read(
                    [], ['id', 'code', 'name']
                ),
                'metals': env['pdp.metal'].with_user(user).search_read(
                    [], ['id', 'name']
                ),
            }
            return self._json_response(data)
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._json_response({'error': str(e)}, status=500)

    # ==========================================================================
    # Helpers
    # ==========================================================================

    def _authenticate_jwt(self):
        """
        Authenticate request via JWT token in Authorization header.
        Returns user record or error Response.
        """
        auth_header = request.httprequest.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return self._json_response({'error': 'Missing or invalid Authorization header'}, status=401)

        token = auth_header[7:]  # Remove 'Bearer '

        try:
            # Verify JWT and get user
            jwt_service = request.env['pdp.api.jwt'].sudo()
            user = jwt_service.verify_token(token)
            if not user:
                return self._json_response({'error': 'Invalid or expired token'}, status=401)
            return user
        except Exception as e:
            _logger.error(f"JWT Auth Error: {e}")
            return self._json_response({'error': 'Authentication failed'}, status=401)

    def _json_response(self, data, status=200):
        """Return a JSON response with proper headers."""
        return Response(
            json.dumps(data, default=str),
            status=status,
            mimetype='application/json',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            }
        )

    def _check_permission(self, user, permission_code):
        """
        Check if user has the required permission.
        Returns None if authorized, or error Response if not.
        """
        try:
            # Try to use pdp.role permission check if available
            role_model = request.env.get('pdp.role')
            if role_model:
                if role_model.sudo().user_has_permission(permission_code, user):
                    return None  # Authorized
                return self._json_response(
                    {'error': f'Permission denied: {permission_code}'},
                    status=403
                )
            # Fallback: allow if pdp_permission module not installed
            return None
        except Exception as e:
            _logger.warning(f"Permission check error: {e}")
            # Fail open if permission system not available
            return None
