import requests

__all__ = ['HubblePaymentAPISession']


class HubblePaymentAPISession(requests.Session):
    """The customized `requests.Session` object.

    ``HubblePaymentAPISession`` helps the ``hubble.payment.PaymentClient``
    create a default ``header``.

    The ``HubblePaymentAPISession`` is initialized in the
    ``hubble.payment.PaymentClient`` constructor.
    """

    def __init__(self):
        super().__init__()

        self.headers.update(
            {
                'Accept-Charset': 'utf-8',
            }
        )

    def init_app_auth(self, m2m_token: str):
        """Initialize the jwt token.

        :param token: The api token user get from webpage.
        """
        auth_header = f'Basic {m2m_token}'
        self.headers.update({'Authorization': auth_header})
