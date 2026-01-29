from odoo import models, api
import json
import logging
import hashlib
import hmac
import base64
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = 'pdp_api_secret_key_change_in_production'  # TODO: Move to ir.config_parameter
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


class PdpApiJwt(models.AbstractModel):
    """
    Simple JWT implementation for API authentication.
    Uses HMAC-SHA256 for signing (no external dependency).
    """
    _name = 'pdp.api.jwt'
    _description = 'PDP API JWT Service'

    @api.model
    def generate_token(self, user):
        """
        Generate a JWT token for the given user.
        """
        now = datetime.utcnow()
        payload = {
            'sub': user.id,
            'login': user.login,
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(hours=JWT_EXPIRATION_HOURS)).timestamp()),
        }
        return self._encode_jwt(payload)

    @api.model
    def verify_token(self, token):
        """
        Verify a JWT token and return the user.
        Returns None if invalid or expired.
        """
        try:
            payload = self._decode_jwt(token)
            if not payload:
                return None

            # Check expiration
            exp = payload.get('exp', 0)
            if datetime.utcnow().timestamp() > exp:
                _logger.warning("JWT token expired")
                return None

            # Get user
            user_id = payload.get('sub')
            if not user_id:
                return None

            user = self.env['res.users'].sudo().browse(user_id)
            if not user.exists() or not user.active:
                return None

            return user
        except Exception as e:
            _logger.error(f"JWT verification error: {e}")
            return None

    def _encode_jwt(self, payload):
        """Encode payload as JWT token."""
        header = {'alg': JWT_ALGORITHM, 'typ': 'JWT'}
        
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload))
        
        signature_input = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            JWT_SECRET_KEY.encode(),
            signature_input.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = self._base64url_encode(signature, is_bytes=True)
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def _decode_jwt(self, token):
        """Decode and verify JWT token."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None

            header_b64, payload_b64, signature_b64 = parts

            # Verify signature
            signature_input = f"{header_b64}.{payload_b64}"
            expected_signature = hmac.new(
                JWT_SECRET_KEY.encode(),
                signature_input.encode(),
                hashlib.sha256
            ).digest()
            expected_signature_b64 = self._base64url_encode(expected_signature, is_bytes=True)

            if not hmac.compare_digest(signature_b64, expected_signature_b64):
                _logger.warning("JWT signature verification failed")
                return None

            # Decode payload
            payload_json = self._base64url_decode(payload_b64)
            return json.loads(payload_json)
        except Exception as e:
            _logger.error(f"JWT decode error: {e}")
            return None

    def _base64url_encode(self, data, is_bytes=False):
        """Base64 URL-safe encoding."""
        if not is_bytes:
            data = data.encode('utf-8')
        encoded = base64.urlsafe_b64encode(data).decode('utf-8')
        return encoded.rstrip('=')

    def _base64url_decode(self, data):
        """Base64 URL-safe decoding."""
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data).decode('utf-8')
