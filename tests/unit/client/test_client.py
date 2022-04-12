import pytest
from hubble import Client
from hubble.excepts import AuthenticationRequiredError


def test_handle_error_request():
    with pytest.raises(AuthenticationRequiredError):
        client = Client(api_token='fake-token')
        client.get_user_info()


def test_client_jsonify():
    client = Client(api_token='fake-token', jsonify=True)
    with pytest.raises(AuthenticationRequiredError):
        resp = client.get_user_info()
        assert isinstance(resp, dict)
