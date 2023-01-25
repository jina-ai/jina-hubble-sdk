import pytest
from mock import patch  # noqa: F401

INTERNAL_APP_ID = 'hubble-sdk'
INTERNAL_PRODUCT_ID = 'hubble-sdk'

PRICE_STRIPE_ID = 'price_1MTl37AkuPxeor9kLZxJ5lfd'

PAYING_USER_ID_1 = '000000000000000000000008'
PAYING_USER_EMAIL_1 = 'andrei.ungureanu@jina.ai'


@pytest.mark.parametrize('user_token', [PAYING_USER_ID_1], indirect=True)
def test_get_summary(stripe_client, payment_client, user_token):

    # creating stripe customer for user
    customer = stripe_client.get_customer(
        PAYING_USER_EMAIL_1, payment_method='pm_card_visa'
    )

    summary = payment_client.get_summary(token=user_token, app_id=INTERNAL_APP_ID)
    expected_result = {'subscriptionItems': [], 'hasPaymentMethod': True}
    assert summary['data'] == expected_result

    # creating subscription
    stripe_client.create_subscription(
        customer_id=customer['customer_id'], items=[PRICE_STRIPE_ID]
    )

    summary = payment_client.get_summary(token=user_token, app_id=INTERNAL_APP_ID)

    expected_result = {
        'subscriptionItems': [
            {
                'internalAppId': 'hubble-sdk',
                'internalProductId': 'hubble-sdk',
                'usageQuantity': 0,
            }
        ],
        'hasPaymentMethod': True,
    }

    assert summary['data'] == expected_result


# def test_submit_usage_report(stripe_client, user_token):
#     pass


# def test_get_authorized_jwt():
#     pass
