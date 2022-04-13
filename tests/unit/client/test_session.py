import pytest
from hubble.client.endpoints import EndpointsV2
from hubble.client.session import HubbleAPISession
from hubble.utils.api_utils import get_base_url


@pytest.fixture
def test_session():
    session = HubbleAPISession()
    yield session
    del session


@pytest.fixture
def init_jwt_auth_url():
    return get_base_url() + EndpointsV2.get_user_info


def test_init_jwt_auth_success_given_valid_api_token(
    test_session, init_jwt_auth_url, requests_mock
):
    requests_mock.post(get_base_url() + EndpointsV2.get_user_info, text='data')
    test_session.init_jwt_auth(api_token='mocked_token')


def test_init_jwt_auth_fail_given_invalid_api_token(test_session):
    test_session.init_jwt_auth(api_token='fake-token')
    assert test_session.headers['Authorization'] == 'token fake-token'
