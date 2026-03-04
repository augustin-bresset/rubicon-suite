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
    # Ornament Categories Endpoints
    # ==========================================================================

    @http.route('/api/v1/pdp/categories', type='http', auth='none',
                methods=['GET'], cors='*', csrf=False)
    def list_categories(self, **kwargs):
        """
        GET /api/v1/pdp/categories
        Returns all ornament categories.
        """
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user

        try:
            categories = request.env['pdp.product.category'].with_user(user).search([])
            data = {
                'categories': [{
                    'id': c.id,
                    'code': c.code,
                    'name': c.name,
                    'waste': c.waste,
                } for c in categories]
            }
            return self._json_response(data)
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/v1/pdp/categories/<int:category_id>', type='http', auth='none',
                methods=['PUT'], cors='*', csrf=False)
    def update_category(self, category_id, **kwargs):
        """
        PUT /api/v1/pdp/categories/<id>
        Body: { "code": "R", "name": "Ring", "waste": 5.0 }
        Updates an ornament category.
        """
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user

        try:
            body = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            category = request.env['pdp.product.category'].with_user(user).browse(category_id)
            
            if not category.exists():
                return self._json_response({'error': 'Category not found'}, status=404)

            vals = {}
            if 'code' in body:
                vals['code'] = body['code']
            if 'name' in body:
                vals['name'] = body['name']
            if 'waste' in body:
                vals['waste'] = float(body['waste'])

            if vals:
                category.write(vals)

            return self._json_response({
                'id': category.id,
                'code': category.code,
                'name': category.name,
                'waste': category.waste,
            })
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/v1/pdp/categories', type='http', auth='none',
                methods=['POST'], cors='*', csrf=False)
    def create_category(self, **kwargs):
        """
        POST /api/v1/pdp/categories
        Body: { "code": "R", "name": "Ring", "waste": 5.0 }
        Creates a new ornament category.
        """
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user

        try:
            body = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            if not body.get('code') or not body.get('name'):
                return self._json_response({'error': 'Code and name are required'}, status=400)

            category = request.env['pdp.product.category'].with_user(user).create({
                'code': body['code'],
                'name': body['name'],
                'waste': float(body.get('waste', 0)),
            })

            return self._json_response({
                'id': category.id,
                'code': category.code,
                'name': category.name,
                'waste': category.waste,
            }, status=201)
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._json_response({'error': str(e)}, status=500)

    @http.route('/api/v1/pdp/categories/<int:category_id>', type='http', auth='none',
                methods=['DELETE'], cors='*', csrf=False)
    def delete_category(self, category_id, **kwargs):
        """
        DELETE /api/v1/pdp/categories/<id>
        Deletes an ornament category.
        """
        user = self._authenticate_jwt()
        if isinstance(user, Response):
            return user

        try:
            category = request.env['pdp.product.category'].with_user(user).browse(category_id)
            
            if not category.exists():
                return self._json_response({'error': 'Category not found'}, status=404)

            category.unlink()
            return self._json_response({'success': True})
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
