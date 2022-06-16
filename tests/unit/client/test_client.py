import pytest
from hubble import Client
from hubble.excepts import AuthenticationRequiredError


@pytest.mark.parametrize('params', [{'jsonify': True}, {'jsonify': False}])
def test_handle_error_request(mocker, params):
    client = Client(**params)

    mocker.patch('hubble.utils.auth.Auth.get_auth_token', return_value=None)
    with pytest.raises(AuthenticationRequiredError):
        client.get_user_info()
