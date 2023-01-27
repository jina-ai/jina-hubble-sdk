import base64
import json

from jose import jwt

from .jwks import JSONWebKeySet


def decode_jwt(token: str):
    """Decode component of JWT

    :param token: base64 encoded JWT component (header or payload)
    """

    decoded = base64.b64decode(token).decode('utf-8')
    try:
        return json.loads(decoded)
    except Exception:
        return decoded


def validate_jwt(token: str):
    """Decode and validate JWT signature against Hubble public key

    :param token: jwt string (as received from Hubble)
    """
    components = token.split('.')
    # NOTE: this is needed because of some base64 decoding errors
    header = decode_jwt(components[0] + "========")

    if header['alg'] != 'ES256':
        raise Exception(f"Algorithm not supported {header['alg']}")

    keys = JSONWebKeySet.get_keys(header['kid'])
    if len(keys) <= 0:
        raise Exception(f"Signing key not found {header['kid']}")

    decoded = jwt.decode(
        token,
        json.dumps(keys[0]),
        algorithms=["ES256"],
        options={"verify_signature": True, "verify_aud": False, "exp": True},
    )
    return decoded
