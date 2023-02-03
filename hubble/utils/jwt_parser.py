import base64
import json

from jose import jwt

from .jwks import JSONWebKeySet


class JWTValidationException(Exception):
    """Raised when JWT validation fails"""

    pass


def decode_jwt_fragment(token: str):
    """Decode component of JWT

    :param token: base64 encoded JWT component (header or payload)
    """
    # NOTE: explicit padding is needed for Python base64 decoding impl
    decoded = base64.urlsafe_b64decode(token + '====').decode('utf-8')
    try:
        return json.loads(decoded)
    except Exception:
        return decoded


def validate_jwt(token: str, aud: str = None):
    """Decode and validate JWT signature against Hubble public key

    :param token: jwt string (as received from Hubble)
    """
    supported_algorithms = ['RS256', 'ES256']
    components = token.split('.')
    header = decode_jwt_fragment(components[0])

    if header['alg'] not in supported_algorithms:
        raise JWTValidationException(f"Algorithm not supported {header['alg']}")

    keys = JSONWebKeySet.get_keys(header['kid'])
    if len(keys) <= 0:
        raise JWTValidationException(f"Signing key not found {header['kid']}")

    try:
        decoded = jwt.decode(
            token,
            json.dumps(keys[0]),
            algorithms=supported_algorithms,
            audience=aud,
            options={
                "verify_signature": True,
                "verify_aud": True if aud else False,
                "exp": True,
            },
        )
    except Exception as e:
        raise JWTValidationException("JWT validation failed") from e

    return decoded


def validate_back_channel_logout_jwt(token: str, aud: str = None):
    """Decode and validate JWT against OIDC back-channel-logout rules

    :param token: jwt string (as received from Hubble)
    """

    decoded = validate_jwt(token, aud)

    try:
        assert ('sub' in decoded) or ('sid' in decoded)
        assert 'http://schemas.openid.net/event/backchannel-logout' in decoded['events']
        assert 'nonce' not in decoded
    except Exception as e:
        # This is not a valid back_channel_logout token
        raise JWTValidationException('Invalid back channel logout token') from e

    return decoded


def validate_back_channel_delete_account_jwt(token: str, aud: str = None):
    """Decode and validate JWT against extended OIDC back-channel-logout for account delete rules

    :param token: jwt string (as received from Hubble)
    """

    decoded = validate_back_channel_logout_jwt(token, aud)

    try:
        assert (
            'http://schemas.openid.net/event/x-backchannel-delete-account'
            in decoded['events']
        )
    except Exception as e:
        raise JWTValidationException('Invalid back channel delete account token') from e

    return decoded
