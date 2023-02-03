import pytest
from hubble.excepts import AuthenticationRequiredError
from hubble.payment.client import PaymentClient


def test_handle_error_request():
    payment_client = PaymentClient(m2m_token='random_m2m_token')
    with pytest.raises(AuthenticationRequiredError):
        payment_client.get_summary(token='random_user_token', app_id='random_app_id')
