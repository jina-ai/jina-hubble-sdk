import json
from typing import IO, Any, MutableMapping, Optional, Text, Union

import requests

from ..utils.api_utils import get_base_url
from .session import HubbleAPISession
from ..excepts import errorcodes


class BaseClient(object):
    """Base Hubble Python API client.

    :param api_token: The api token user get from webpage.
    :param max_retries: Number of allowed maximum retries.
    :param timeout: Number of timeout, in seconds.
    :param jsonify: Convert `requests.Response` object to json.
    """

    def __init__(
        self,
        api_token: str,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
        jsonify: bool = False,
    ):
        self._api_token = api_token
        self._session = HubbleAPISession()
        self._session.init_jwt_auth(api_token=api_token)
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
        code = resp.get('code', -1)
        data = resp.get('data', {})

        ExceptionCls = errorcodes[code]

        raise ExceptionCls(response=resp, data=data, message=message, code=code)

    def handle_request(
        self,
        url: str,
        method='POST',
        data: Optional[dict] = None,
        files: Optional[MutableMapping[Text, IO[Any]]] = None,
    ) -> Union[requests.Response, dict]:
        """The basis request handler.

        Hubble API consider all requests as POST requests.
        The method leverage the ``HubbleAPISession`` to send
        POST requests based on parameters.

        :param url: The url of the request.
        :param method: The request type, fow v2 always set to POST.
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
