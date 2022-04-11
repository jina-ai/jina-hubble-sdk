import requests

from ..utils import get_base_url
from .endpoints import Endpoints

__all__ = ['HubbleAPISession']


class HubbleAPISession(requests.Session):
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
                'Content-Type': 'text/json',
            }
        )

    def init_jwt_auth(self, api_token: str):
        """Initialize the jwt token and perform validation.

        :param api_token: The api token user get from webpage.
        """
        self.headers.update({'Authorization': f'token {api_token}'})
        assert self._validate_api_token().ok

    def _validate_api_token(self) -> requests.Response:
        """Valid if the api token.

        This function will call the whoami endpoint from Hubble API
        to get user info.

        :return: a `requests.Response` object from Hubble API server.
        """
        import requests

        url = get_base_url() + Endpoints.get_user_info
        try:
            resp = requests.post(url, headers=self.headers)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise e
        return resp
