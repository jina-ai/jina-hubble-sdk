import base64
import json
import logging
import uuid
from typing import Optional

import requests
from jose import jwt

# TODO: add payment specific errorcodes
from ..excepts import errorcodes
from ..utils.api_utils import get_base_url, get_json_from_response
from .jwks import JSONWebKeySet
from .session import HubblePaymentAPISession


class PaymentBaseClient(object):
    """Hubble Payment Python API client."""

    def __init__(self, m2m_token: str):
        self._base_url = get_base_url()
        # initalize session using app token
        self._session = HubblePaymentAPISession()
        self._session.init_app_auth(m2m_token=m2m_token)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _handle_error_request(self, resp: dict):
        if isinstance(resp, requests.Response):
            resp = get_json_from_response(resp)

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
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        log_error: Optional[bool] = True,
    ) -> dict:
        """The basis request handler.

        Hubble API consider all requests as POST requests.
        The method leverages the ``HubbleAPISession`` to send
        POST requests based on parameters.

        :param url: The url of the request.
        :param method: The request type, for v2 always set to POST.
        :param data: Optional data payloads to be send along with request.
        :returns: dict.
        """

        default_headers = {'jinameta-session-id': str(uuid.uuid1())}
        if headers:
            headers.update(default_headers)
        else:
            headers = default_headers

        session_id = headers.get('jinameta-session-id')

        try:
            # making request to hubble
            resp = self._session.request(
                method=method,
                url=url,
                data=data if data else None,
                headers=headers,
                json=json if json else None,
            )

            if resp.status_code >= 400:
                self._handle_error_request(resp)

            resp = get_json_from_response(resp)

        except Exception as e:

            # this might not be necessary
            if log_error:
                self.logger.error(
                    f'Please report this session_id: {session_id} to Hubble'
                )

            raise e

        return resp

    def decode_jwt(self, token: str):
        """Decode component of JWT

        :param token: base64 encoded JWT component (header or payload)
        """

        decoded = base64.b64decode(token).decode('utf-8')
        try:
            return json.loads(decoded)
        except Exception:
            return decoded

    def validate_jwt(self, token: str):
        """Decode and validate JWT signature against Hubble public key

        :param token: jwt string (as received from Hubble)
        """
        components = token.split('.')
        # NOTE: this is needed because of some base64 decoding errors
        header = self.decode_jwt(components[0] + "========")
        if header['alg'] != 'ES256':
            raise Exception(f"Algorithm not supported {header['alg']}")
        keys = JSONWebKeySet.get_keys(header['kid'])
        if len(keys) <= 0:
            raise Exception(f"Signing key not found {header['kid']}")
        try:
            decoded = jwt.decode(
                token,
                json.dumps(keys[0]),
                algorithms=["ES256"],
                options={"verify_signature": True, "verify_aud": False, "exp": True},
            )
            return decoded
        except Exception:
            raise Exception("Invalid JWT")
