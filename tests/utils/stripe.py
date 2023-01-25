import time
from datetime import datetime
from typing import List


def wait(secs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            time.sleep(secs)
            return result

        return wrapper

    return decorator


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

    @wait(2)
    def create_clock(self):
        now = datetime.now()
        unix_time = now.timestamp()
        unix_time = int(unix_time)

        return self._stripe.test_helpers.TestClock.create(frozen_time=unix_time)

    @wait(2)
    def advance_clock(self, test_clock_id: str, date: datetime):
        # https://stripe.com/docs/api/test_clocks/advance?lang=python
        unix_time = date.timestamp()
        unix_time = int(unix_time)

        test_clock = self._stripe.test_helpers.TestClock.advance(
            test_clock_id, frozen_time=unix_time
        )

        # waiting for test_clock to finish advancing
        while test_clock['status'] == 'advancing':
            time.sleep(0.5)
            test_clock = self._stripe.test_helpers.TestClock.retrieve(test_clock_id)

        return test_clock

    @wait(2)
    def delete_clock(self, test_clock_id: str):
        return self._stripe.test_helpers.TestClock.delete(test_clock_id)

    @wait(2)
    def create_customer(self, email: str, test_clock_id: str, payment_method=None):
        return self._stripe.Customer.create(
            email=email, test_clock=test_clock_id, payment_method=payment_method
        )

    @wait(2)
    def create_subscription(self, customer_id: str, items: List[str]):
        # https://stripe.com/docs/api/subscriptions/create?lang=python
        subscription_items = [{'price': item} for item in items]

        return self._stripe.Subscription.create(
            customer=customer_id, items=subscription_items
        )

    def get_customer(self, email: str, payment_method: str = None):

        if email in self.cache:
            return self.cache[email]

        test_clock = self.create_clock()
        test_clock_id = test_clock['id']

        customer = self.create_customer(
            email=email, test_clock_id=test_clock_id, payment_method=payment_method
        )
        customer_id = customer['id']

        self.cache[email] = {'customer_id': customer_id, 'test_clock_id': test_clock_id}

        return self.cache[email]

    # TODO: finish this function
    def cleanup(self):
        pass
