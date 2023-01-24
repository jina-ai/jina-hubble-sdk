import time
from datetime import datetime, timestamp
from typing import List


class StripeClient(object):
    """Stripe utility functions for testing"""

    def __init__(self, stripe_key: str):
        try:
            import stripe

            self._stripe = stripe
            self._stripe.api_key = stripe_key
        except Exception:
            raise Exception('Failed to initialize stripe, make sure it is installed.')

        self.cache = {}

    # stripe helpers

    def create_clock(self):
        now = datetime.now()
        unix_time = timestamp(now) * 1000

        return self._stripe.test_helpers.TestClock.create(frozen_time=unix_time)

    def advance_clock(self, clock_id: str, date: datetime):
        # https://stripe.com/docs/api/test_clocks/advance?lang=python
        unix_time = timestamp(date) * 1000
        test_clock = self._stripe.test_helpers.TestClock.advance(
            clock_id, frozen_time=unix_time
        )

        # waiting for test_clock to finish advancing
        while test_clock['status'] == 'advancing':
            time.sleep(0.5)
            test_clock = self._stripe.test_helpers.TestClock.retrieve(clock_id)

        return test_clock

    def delete_clock(self, clock_id: str):
        return self._stripe.test_helpers.TestClock.delete(clock_id)

    # TODO: add the ability to create customer with payment method
    def create_customer(self, email: str, clock_id: str, payment_method=None):
        return self._stripe.Customer.create(
            email=email, test_clock_id=clock_id, payment_method=payment_method
        )

    # NOTE: doesn't seem to be necessary for now
    # def delete_customer(self, customer_id: str):
    #     return setl._stripe.Customer.delete(customer_i)

    def create_subscription(self, customer_id: str, items: List[str]):
        # https://stripe.com/docs/api/subscriptions/create?lang=python
        subscription_items = [{'price': item} for item in items]
        return self._stripe.Subscription.create(
            customer=customer_id, items=subscription_items
        )

    # NOTE: doesn't seem to be necessary for now
    # def delete_subscription(self, subscription_id: str):
    #     # https://stripe.com/docs/api/subscriptions/cancel?lang=python
    #     return self._stripe.Subscription.delete(subscription_id)

    # test helpers

    def get_customer(self, email: str, payment_method: str = None):

        if email in self.cache:
            return self.cache[email]

        test_clock = self.create_clock()
        test_clock_id = test_clock['id']

        customer = self.create_customer(
            email, test_clock_id, payment_method=payment_method
        )
        customer_id = customer['id']

        self.cache[email] = {'customer_id': customer_id, 'test_clock_id': test_clock_id}

        return self.cache[email]

    # TODO: finish this function
    def cleanup(self):
        pass
