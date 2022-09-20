from typing import IO, Any, MutableMapping, Optional, Text, Union

import requests

from ..excepts import errorcodes
from ..utils.api_utils import get_base_url
from ..utils.auth import Auth
from .session import HubbleAPISession


class BaseClient(object):
    """Base Hubble Python API client.

    :param max_retries: Number of allowed maximum retries.
    :param jsonify: Convert `requests.Response` object to json.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        max_retries: Optional[int] = None,
        jsonify: bool = False,
    ):
        self._session = HubbleAPISession()

        self._token = token if token else Auth.get_auth_token()
        if self._token:
            self._session.init_jwt_auth(token=self._token)

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
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
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
            or dict if jsonify.
        """
        resp = self._session.request(
            method=method,
            url=url,
            data=data if data else None,
            files=files,
            headers=headers,
            json=json if json else None,
        )
        if resp.status_code >= 400:
            self._handle_error_request(resp)

        if self._jsonify:
            return resp.json()

        return resp
