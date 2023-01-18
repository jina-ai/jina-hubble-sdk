import pytest
from hubble.excepts import AuthenticationRequiredError
from hubble.payment.client import PaymentClient
from jose import jwt
from mock import patch  # noqa: F401

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


def test_handle_error_request():
    payment_client = PaymentClient(m2m_token='random_m2m_token')
    with pytest.raises(AuthenticationRequiredError):
        payment_client.get_summary(token='random_user_token', app_id='random_app_id')


def test_decode_jwt():
    payment_client = PaymentClient(m2m_token='random_m2m_token')

    payload = {
        'iss': 'http://localhost:3000',
        'aud': 'random_audience_id',
        'sub': 'random_user_id',
        'token': 'random_user_token',
    }

    token = jwt.encode(payload, 'secret', algorithm='HS256')
    token_components = token.split('.')
    token_payload = payment_client.decode_jwt(token_components[1] + "========")
    assert token_payload == payload


@pytest.mark.parametrize(
    'args',
    [
        {
            'private_key': PRIVATE_KEY,
            'public_key': PUBLIC_KEY,
            'should_throw_error': False,
        },
        {
            'private_key': PRIVATE_KEY,
            'public_key': OTHER_PUBLIC_KEY,
            'should_throw_error': True,
        },
    ],
)
def test_validate_jwt(mocker, args):

    mocker.patch(
        'hubble.payment.jwks.JSONWebKeySet.get_keys', return_value=[args['public_key']]
    )

    payment_client = PaymentClient(m2m_token='random_m2m_token')

    headers = {'kid': PUBLIC_KEY['kid']}

    payload = {
        'iss': 'http://localhost:3000',
        'aud': 'random_audience_id',
        'sub': 'random_user_id',
        'token': 'random_user_token',
    }

    token = jwt.encode(payload, args['private_key'], algorithm='ES256', headers=headers)

    if args['should_throw_error']:
        with pytest.raises(Exception):
            payment_client.validate_jwt(token=token)
    else:
        decoded_token = payment_client.validate_jwt(token=token)
        assert decoded_token == payload
