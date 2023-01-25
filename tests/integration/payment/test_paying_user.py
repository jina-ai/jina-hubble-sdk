import time

import pytest
from mock import patch  # noqa: F401

INTERNAL_APP_ID = 'hubble-sdk'
INTERNAL_PRODUCT_ID = 'hubble-sdk'

PRICE_STRIPE_ID = 'price_1MTl37AkuPxeor9kLZxJ5lfd'

PAYING_USER_ID_1 = '63d0dd0ef4b40caaaf7edc12'
PAYING_USER_EMAIL_1 = 'hubble_sdk_user_1@jina.ai'

PAYING_USER_ID_2 = '63d0dd28f4b40caaaf7edc14'
PAYING_USER_EMAIL_2 = 'hubble_sdk_user_2@jina.ai'


@pytest.mark.parametrize('user_token', [PAYING_USER_ID_1], indirect=True)
def test_get_summary(stripe_client, payment_client, user_token):

    # creating stripe customer for user
    customer = stripe_client.get_customer(
        email=PAYING_USER_EMAIL_1, payment_method='pm_card_visa'
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
                'internalAppId': INTERNAL_APP_ID,
                'internalProductId': INTERNAL_PRODUCT_ID,
                'usageQuantity': 0,
            }
        ],
        'hasPaymentMethod': True,
    }

    assert summary['data'] == expected_result


@pytest.mark.parametrize('user_token', [PAYING_USER_ID_2], indirect=True)
def test_submit_usage_report(stripe_client, payment_client, user_token):

    # try to submit a usage report
    customer = stripe_client.get_customer(
        email=PAYING_USER_EMAIL_2, payment_method='pm_card_visa'
    )

    stripe_client.create_subscription(
        customer_id=customer['customer_id'], items=[PRICE_STRIPE_ID]
    )

    payment_client.report_usage(
        token=user_token,
        app_id=INTERNAL_APP_ID,
        product_id=INTERNAL_PRODUCT_ID,
        quantity=1,
    )

    # NOTE: sleeping to wait for the usage report to be processed
    # TODO: PR Hubble to process usage faster on the staging environment (every 10-15 seconds)
    time.sleep(15)

    summary = payment_client.get_summary(token=user_token, app_id=INTERNAL_APP_ID)

    expected_result = {
        'subscriptionItems': [
            {
                'internalAppId': INTERNAL_APP_ID,
                'internalProductId': INTERNAL_PRODUCT_ID,
                'usageQuantity': 1,
            }
        ],
        'hasPaymentMethod': True,
    }

    assert summary['data'] == expected_result


# def test_get_authorized_jwt():
#     pass
