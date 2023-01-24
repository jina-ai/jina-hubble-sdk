import os
import tempfile

import pytest
from hubble.payment.client import PaymentClient

from .utils.stripe import StripeClient


@pytest.fixture(autouse=True)
def tmpfile(tmpdir):
    tmpfile = f'jina_test_{next(tempfile._get_candidate_names())}.db'
    return tmpdir / tmpfile


@pytest.fixture(scope='session')
def m2m_token():
    return os.environ.get('M2M_TOKEN', None)


# fixture for acquiring a 'cached' instance of StripeClient
@pytest.fixture(scope='session')
def stripe_client():
    api_key = os.environ.get('stripe_secret_key', None)
    client = StripeClient(api_key)
    yield client
    client.cleanup()


@pytest.fixture()
def payment_client(m2m_token):
    payment_client = PaymentClient(m2m_token=m2m_token)
    yield payment_client


@pytest.fixture()
def user_token(payment_client, user_id):
    user_token = payment_client.get_user_token(user_id=user_id)
    yield user_token
