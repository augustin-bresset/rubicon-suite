import json
import logging

from odoo import http, SUPERUSER_ID
from odoo.http import request, Response
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

# JWT Configuration (should match model)
JWT_EXPIRATION_HOURS = 24


class PdpApiAuthController(http.Controller):
    """
    Authentication endpoints for JWT.
    """

    @http.route('/api/v1/auth/login', type='http', auth='none',
                methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def login(self, **kwargs):
        """
        POST /api/v1/auth/login
        Body: { "login": "user", "password": "pass" }
        Returns: { "token": "...", "user": {...} }
        """
        # Handle CORS preflight
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        try:
            body = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            login_name = body.get('login')
            password = body.get('password')

            if not login_name or not password:
                return self._json_response({'error': 'Login and password required'}, status=400)

            # Get database from request
            db = request.db
            if not db:
                return self._json_response({'error': 'Database not configured'}, status=500)

            # Manual authentication for Odoo 18
            from odoo.modules.registry import Registry
            from passlib.context import CryptContext
            
            reg = Registry(db)
            with reg.cursor() as cr:
                from odoo.api import Environment
                env = Environment(cr, SUPERUSER_ID, {})
                
                # Find user by login
                user = env['res.users'].search([
                    ('login', '=', login_name),
                    ('active', '=', True)
                ], limit=1)
                
                if not user:
                    _logger.warning(f"Login failed: user '{login_name}' not found")
                    return self._json_response({'error': 'Invalid credentials'}, status=401)
                
                # Get password hash from database
                cr.execute('SELECT password FROM res_users WHERE id = %s', (user.id,))
                result = cr.fetchone()
                if not result or not result[0]:
                    _logger.warning(f"Login failed: no password for user '{login_name}'")
                    return self._json_response({'error': 'Invalid credentials'}, status=401)
                
                stored_hash = result[0]
                
                # Verify password using passlib
                ctx = CryptContext(['pbkdf2_sha512', 'plaintext'], deprecated=['plaintext'])
                if not ctx.verify(password, stored_hash):
                    _logger.warning(f"Login failed: invalid password for user '{login_name}'")
                    return self._json_response({'error': 'Invalid credentials'}, status=401)
                
                _logger.info(f"Login successful for user '{login_name}'")
                
                # Generate JWT
                jwt_service = env['pdp.api.jwt']
                token = jwt_service.generate_token(user)

                return self._json_response({
                    'token': token,
                    'expires_in': JWT_EXPIRATION_HOURS * 3600,
                    'user': {
                        'id': user.id,
                        'login': user.login,
                        'name': user.name,
                    }
                })
        except Exception as e:
            _logger.error(f"Login error: {e}")
            import traceback
            _logger.error(traceback.format_exc())
            return self._json_response({'error': 'Authentication failed'}, status=500)

    @http.route('/api/v1/auth/refresh', type='http', auth='none',
                methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def refresh(self, **kwargs):
        """
        POST /api/v1/auth/refresh
        Header: Authorization: Bearer <token>
        Returns new token.
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        auth_header = request.httprequest.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return self._json_response({'error': 'Missing Authorization header'}, status=401)

        token = auth_header[7:]
        jwt_service = request.env['pdp.api.jwt'].sudo()
        user = jwt_service.verify_token(token)

        if not user:
            return self._json_response({'error': 'Invalid or expired token'}, status=401)

        new_token = jwt_service.generate_token(user)
        return self._json_response({
            'token': new_token,
            'expires_in': JWT_EXPIRATION_HOURS * 3600,
        })

    @http.route('/api/v1/auth/me', type='http', auth='none',
                methods=['GET', 'OPTIONS'], cors='*', csrf=False)
    def me(self, **kwargs):
        """
        GET /api/v1/auth/me
        Returns current user info.
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        auth_header = request.httprequest.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return self._json_response({'error': 'Missing Authorization header'}, status=401)

        token = auth_header[7:]
        jwt_service = request.env['pdp.api.jwt'].sudo()
        user = jwt_service.verify_token(token)

        if not user:
            return self._json_response({'error': 'Invalid or expired token'}, status=401)

        return self._json_response({
            'id': user.id,
            'login': user.login,
            'name': user.name,
            'email': user.email,
        })

    def _json_response(self, data, status=200):
        """Return a JSON response."""
        return Response(
            json.dumps(data, default=str),
            status=status,
            mimetype='application/json',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            }
        )

    def _cors_response(self):
        """Return CORS preflight response."""
        return Response(
            '',
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            }
        )
