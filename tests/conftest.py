import tempfile

import pytest
from jose import jwt


@pytest.fixture(autouse=True)
def tmpfile(tmpdir):
    tmpfile = f'jina_test_{next(tempfile._get_candidate_names())}.db'
    return tmpdir / tmpfile


@pytest.fixture()
def generate_jwt(mocker):
    private_key = {
        "kty": "EC",
        "d": "iLw805NZwMRKwcXOmtDPGlB158S_PUkRVnlbmEMmO2E",
        "use": "sig",
        "crv": "P-256",
        "kid": "AO78Ls0d2WgEYpwUF1qv_TcBytohycSLByU5ugY7Fp8",
        "x": "KmpjXcs-ZoVBTqhzI5rlTqq0-BASZUOUINkYCcZG9K8",
        "y": "z-jGVJXhv1pfh_ic8wWTE30p_2JT0aTshfxx_TtiMm0",
        "alg": "ES256",
    }

    public_key = {
        "kty": "EC",
        "use": "sig",
        "crv": "P-256",
        "kid": "AO78Ls0d2WgEYpwUF1qv_TcBytohycSLByU5ugY7Fp8",
        "x": "KmpjXcs-ZoVBTqhzI5rlTqq0-BASZUOUINkYCcZG9K8",
        "y": "z-jGVJXhv1pfh_ic8wWTE30p_2JT0aTshfxx_TtiMm0",
        "alg": "ES256",
    }

    headers = {'kid': public_key['kid']}

    mocker.patch('hubble.utils.jwks.JSONWebKeySet.get_keys', return_value=[public_key])

    def encode(payload):
        return jwt.encode(payload, private_key, algorithm='ES256', headers=headers)

    return encode
