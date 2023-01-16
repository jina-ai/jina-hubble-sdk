import requests

__all__ = ['HubblePaymentAPISession']


class HubblePaymentAPISession(requests.Session):
    """The customized `requests.Session` object.

    ``HubbleAPISession`` helps the ``hubble.client.Client`` create a default
    ``header`` and validate the jwt token when calling ``init_jwt_auth``.

    The ``HubbleAPISession`` is initialized in the ``hubble.client.Client``
    constructor.
    """

    def __init__(self):
        super().__init__()

        self.headers.update(
            {
                'Accept-Charset': 'utf-8',
            }
        )

    def init_app_auth(self, token: str):
        """Initialize the jwt token.

        :param token: The api token user get from webpage.
        """
        auth_header = f'Basic {token}'
        self.headers.update({'Authorization': auth_header})
