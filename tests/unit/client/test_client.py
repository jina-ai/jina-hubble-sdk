import os

import hubble
import pytest
from hubble import Client, login_required
from hubble.excepts import AuthenticationRequiredError
from mock import patch


@patch.dict(os.environ, {'JINA_AUTH_TOKEN': ''})
@pytest.mark.parametrize('params', [{'jsonify': True}, {'jsonify': False}])
def test_handle_error_request(mocker, params):
    client = Client(**params)

    mocker.patch('hubble.utils.auth.Auth.get_auth_token', return_value=None)
    with pytest.raises(AuthenticationRequiredError):
        client.get_user_info()


@patch.dict(os.environ, {'JINA_AUTH_TOKEN': ''})
def test_auth_required_decorator_no_token():
    @login_required
    def foo():
        print('hello!!!')

    with pytest.raises(AuthenticationRequiredError):
        foo()


@patch.dict(os.environ, {'JINA_AUTH_TOKEN': 'abc'})
def test_auth_required_decorator_success():
    patch('hubble.login_required', lambda x: x).start()

    @hubble.login_required
    def foo():
        print('hello!!!')

    foo()


@patch.dict(os.environ, {'JINA_AUTH_TOKEN': 'somerandomtoken'})
def test_auth_required_decorator_wrong_or_expired_token():
    @login_required
    def foo():
        print('hello!!!')

    with pytest.raises(AuthenticationRequiredError):
        foo()


def test_get_user_info_via_jwt(generate_jwt):
    user_payload = {
        '_id': 'random_user_id',
        'status': 'active',
    }

    client = Client(token=generate_jwt({'user': user_payload}))

    user = client.get_user_info(variant='data')
    assert user == {
        '_id': 'random_user_id',
        'status': 'active',
    }
