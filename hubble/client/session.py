from requests import Session

from ..utils import get_base_url

__all__ = ['HubbleAPISession']


class HubbleAPISession(Session):
    def __init__(self, *args, **kwargs):
        """
        Creates a new HubbleAPISession instance.
        """
        super(HubbleAPISession, self).__init__(*args, **kwargs)

        self.headers.update(
            {
                'Accept-Charset': 'utf-8',
                'Content-Type': 'text/json',
            }
        )

    def init_jwt_auth(self, api_token):
        self.headers.update({'Authorization': f'token {api_token}'})
        assert self._validate_api_token().ok

    def _validate_api_token(self):
        import requests

        url = get_base_url() + 'user.identity.whoami'
        try:
            resp = requests.post(url, headers=self.headers)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise e
        return resp
