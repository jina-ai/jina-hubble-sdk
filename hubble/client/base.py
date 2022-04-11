from typing import Optional, Text, Any, IO, MutableMapping

import requests

from .session import HubbleAPISession
from ..utils.api_utils import get_base_url


class BaseClient(object):
    def __init__(
        self,
        api_token: str,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """"""
        self._api_token = api_token
        self._session = HubbleAPISession()
        self._session.init_jwt_auth(api_token=api_token)
        self._timeout = timeout
        self._base_url = get_base_url()
        if max_retries:
            from requests.adapters import HTTPAdapter

            self._session.mount(
                prefix=self._base_url, adapter=HTTPAdapter(max_retries=max_retries)
            )

    def _handle_error_request(self, resp: requests.Response):
        pass

    def handle_request(
        self,
        url: str,
        method='POST',
        data: Optional[dict] = None,
        files: MutableMapping[Text, IO[Any]] = None,
    ):
        resp = self._session.request(
            method=method,
            url=url,
            data=data,
            timeout=self._timeout,
            files=files,
        )
        if resp.status_code >= 400:
            self._handle_error_request(resp)

        return resp.json()
