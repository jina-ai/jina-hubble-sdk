import pytest
from hubble import Client
from hubble.excepts import AuthenticationRequiredError


def test_handle_error_request():
    with pytest.raises(AuthenticationRequiredError):
        client = Client()
        client.get_user_info()


def test_client_jsonify():
    client = Client(jsonify=True)
    resp = client.get_user_info()
    assert isinstance(resp, str)
