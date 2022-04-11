import pytest
import requests
from hubble.client.endpoints import Endpoints
from hubble.client.session import HubbleAPISession
from hubble.utils.api_utils import get_base_url


@pytest.fixture
def test_session():
    return HubbleAPISession()


@pytest.fixture
def init_jwt_auth_url():
    return get_base_url() + Endpoints.get_user_info


def test_init_jwt_auth_success_given_correct_api_token(test_session, init_jwt_auth_url):
    pass


def test_init_jwt_auth_fail_given_incorrect_api_token(test_session):
    with pytest.raises(requests.exceptions.HTTPError):
        test_session.init_jwt_auth(api_token='fake_token')
