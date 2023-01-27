import pytest
from hubble.excepts import AuthenticationRequiredError
from hubble.payment.client import PaymentClient
from hubble.utils.jwt_parser import decode_jwt, validate_jwt
from jose import jwt

PRIVATE_KEY = {
    "kty": "EC",
    "d": "iLw805NZwMRKwcXOmtDPGlB158S_PUkRVnlbmEMmO2E",
    "use": "sig",
    "crv": "P-256",
    "kid": "AO78Ls0d2WgEYpwUF1qv_TcBytohycSLByU5ugY7Fp8",
    "x": "KmpjXcs-ZoVBTqhzI5rlTqq0-BASZUOUINkYCcZG9K8",
    "y": "z-jGVJXhv1pfh_ic8wWTE30p_2JT0aTshfxx_TtiMm0",
    "alg": "ES256",
}

PUBLIC_KEY = {
    "kty": "EC",
    "use": "sig",
    "crv": "P-256",
    "kid": "AO78Ls0d2WgEYpwUF1qv_TcBytohycSLByU5ugY7Fp8",
    "x": "KmpjXcs-ZoVBTqhzI5rlTqq0-BASZUOUINkYCcZG9K8",
    "y": "z-jGVJXhv1pfh_ic8wWTE30p_2JT0aTshfxx_TtiMm0",
    "alg": "ES256",
}

OTHER_PUBLIC_KEY = {
    "kty": "EC",
    "use": "sig",
    "crv": "P-256",
    "kid": "t-_9dLjYMVjPJ44_4aRGqAm58KpHXnAh5XktKlkKUSQ",
    "x": "_KCLiE8ul1eTVWdObu31mF26a3BzIsP2G6b2wPYlHFA",
    "y": "N6e_WdVrjjxVPZScBVLdluPk91pqoDRyS1BZ0ImDzPI",
    "alg": "ES256",
}

HEADERS = {'kid': PUBLIC_KEY['kid']}

PAYLOAD = {
    'iss': 'http://localhost:3000',
    'aud': 'random_audience_id',
    'sub': 'random_user_id',
    'token': 'random_user_token',
}


def test_handle_error_request():
    payment_client = PaymentClient(m2m_token='random_m2m_token')
    with pytest.raises(AuthenticationRequiredError):
        payment_client.get_summary(token='random_user_token', app_id='random_app_id')


def test_decode_jwt():
    token = jwt.encode(PAYLOAD, 'secret', algorithm='HS256')
    token_components = token.split('.')
    token_payload = decode_jwt(token_components[1] + "========")
    assert token_payload == PAYLOAD


def test_validate_jwt_success(mocker):

    mocker.patch('hubble.utils.jwks.JSONWebKeySet.get_keys', return_value=[PUBLIC_KEY])

    token = jwt.encode(PAYLOAD, PRIVATE_KEY, algorithm='ES256', headers=HEADERS)
    decoded_token = validate_jwt(token=token)
    assert decoded_token == PAYLOAD


def test_validate_jwt_failure(mocker):

    mocker.patch(
        'hubble.utils.jwks.JSONWebKeySet.get_keys', return_value=[OTHER_PUBLIC_KEY]
    )

    token = jwt.encode(PAYLOAD, PRIVATE_KEY, algorithm='ES256', headers=HEADERS)
    with pytest.raises(Exception):
        validate_jwt(token=token)
