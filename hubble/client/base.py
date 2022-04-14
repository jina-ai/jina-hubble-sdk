import json
from typing import IO, Any, MutableMapping, Optional, Text, Union

import requests

from ..excepts import errorcodes
from ..utils.api_utils import get_base_url
from ..utils.auth import Auth
from .session import HubbleAPISession


class BaseClient(object):
    """Base Hubble Python API client.

    :param max_retries: Number of allowed maximum retries.
    :param timeout: Request timeout, in seconds.
    :param jsonify: Convert `requests.Response` object to json.
    """

    def __init__(
        self,
        max_retries: Optional[int] = None,
        timeout: int = 10,
        jsonify: bool = False,
    ):
        self._api_token = Auth.get_auth_token()
        if not self._api_token:
            raise ValueError(
                'We can not get the token, please call `hubble.login()` first.'
            )
        self._session = HubbleAPISession()
        self._session.init_jwt_auth(api_token=self._api_token)
        self._timeout = timeout
        self._base_url = get_base_url()
        self._jsonify = jsonify
        if max_retries:
            from requests.adapters import HTTPAdapter

            self._session.mount(
                prefix=self._base_url, adapter=HTTPAdapter(max_retries=max_retries)
            )

    def _handle_error_request(self, resp: Union[requests.Response, dict]):
        if isinstance(resp, requests.Response):
            resp = resp.json()

        message = resp.get('message', None)
        code = resp.get('status', -1)
        data = resp.get('data', {})

        ExceptionCls = errorcodes[code]

        raise ExceptionCls(response=resp, data=data, message=message, code=code)

    def handle_request(
        self,
        url: str,
        method: str = 'POST',
        data: Optional[dict] = None,
        files: Optional[MutableMapping[Text, IO[Any]]] = None,
    ) -> Union[requests.Response, dict]:
        """The basis request handler.

        Hubble API consider all requests as POST requests.
        The method leverages the ``HubbleAPISession`` to send
        POST requests based on parameters.

        :param url: The url of the request.
        :param method: The request type, for v2 always set to POST.
        :param data: Optional data payloads to be send along with request.
        :param files: Optional files to be uploaded.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        resp = self._session.request(
            method=method,
            url=url,
            data=data if data else None,
            timeout=self._timeout,
            files=files,
        )
        if resp.status_code >= 400:
            self._handle_error_request(resp)

        if self._jsonify:
            resp = json.dumps(resp.json(), indent=2)

        return resp
