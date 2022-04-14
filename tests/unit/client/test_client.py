import pytest
from hubble import Client
from hubble.excepts import AuthenticationRequiredError


def test_handle_error_request(mocker):
    mocker.patch('hubble.utils.auth.Auth.get_auth_token', return_value='fake-token')
    with pytest.raises(AuthenticationRequiredError):
        client = Client()
        client.get_user_info()


def test_client_jsonify(mocker):
    mocker.patch('hubble.utils.auth.Auth.get_auth_token', return_value='fake-token')
    with pytest.raises(AuthenticationRequiredError):
        client = Client(jsonify=True)
        resp = client.get_user_info()
        assert isinstance(resp, str)
