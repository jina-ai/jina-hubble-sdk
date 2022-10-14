import json
import os

import aiohttp
import pytest
import requests
from hubble.utils.auth import Auth
from hubble.utils.config import config


class AuthorizeResponse:

    _authorization_response = {
        'event': 'authorize',
        'data': {
            'code': 'SOME_CODE',
            'state': 'SOME_STATE',
        },
    }

    _error_response = {'event': 'error', 'data': {}}

    def __init__(self, *args, status_code=200, **kwargs):
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *error_info):
        return self

    @property
    async def content(self):
        if self.status_code == 200:
            yield json.dumps(self._authorization_response).encode('utf-8')
        else:
            yield json.dumps(self._error_response).encode('utf-8')


class AuthorizeResponseSync:

    _authorization_response = {
        'event': 'authorize',
        'data': {
            'code': 'SOME_CODE',
            'state': 'SOME_STATE',
        },
    }

    _error_response = {'event': 'error', 'data': {}}

    def __init__(self, *args, status_code=200, **kwargs):
        self.status_code = status_code

    def iter_lines(self):
        if self.status_code == 200:
            yield json.dumps(self._authorization_response).encode('utf-8')
        else:
            yield json.dumps(self._error_response).encode('utf-8')


class GrantResponse:

    _grant_response = {
        'data': {'token': 'SOME_TOKEN', 'user': {'nickname': 'SOME_NICKNAME'}}
    }

    _error_response = {}

    def __init__(self, *args, status_code=200, **kwargs):
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *error_info):
        return self

    async def json(self):
        if self.status_code == 200:
            return self._grant_response
        else:
            return self._error_response

    def raise_for_status(self):
        if not self.status_code == 200:
            raise aiohttp.ClientResponseError()


class GrantResponseSync:

    _grant_response = {
        'data': {'token': 'SOME_TOKEN', 'user': {'nickname': 'SOME_NICKNAME'}}
    }

    _error_response = {}

    def __init__(self, *args, status_code=200, **kwargs):
        self.status_code = status_code

    def json(self):
        if self.status_code == 200:
            return self._grant_response
        else:
            return self._error_response

    def raise_for_status(self):
        if not self.status_code == 200:
            raise requests.ClientResponseError()


class ValidateResponse:

    _validate_response = {}

    _error_response = {}

    def __init__(self, *args, status_code=200, **kwargs):
        self.status_code = status_code

    def raise_for_status(self):
        if not self.status_code == 200:
            raise requests.exceptions.HTTPError()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'existing_token, expected_token, validate_status_code, force',
    [
        ['EXISTING_TOKEN', 'SOME_TOKEN', 200, True],
        ['EXISTING_TOKEN', 'EXISTING_TOKEN', 200, False],
        ['EXISTING_TOKEN', 'SOME_TOKEN', 400, False],
        [None, 'SOME_TOKEN', 200, True],
        [None, 'SOME_TOKEN', 200, False],
    ],
)
async def test_login_logout(
    mocker, monkeypatch, existing_token, expected_token, validate_status_code, force
):
    def _mock_get_aiohttp(*args, **kwargs):
        mock_response = AuthorizeResponse(status_code=200)
        return mock_response

    def _mock_post_aiohttp(*args, **kwargs):
        mock_response = GrantResponse(status_code=200)
        return mock_response

    def _mock_post_requests(*args, **kwargs):
        mock_response = ValidateResponse(status_code=validate_status_code)
        return mock_response

    monkeypatch.setattr('aiohttp.ClientSession.get', _mock_get_aiohttp)
    monkeypatch.setattr('aiohttp.ClientSession.post', _mock_post_aiohttp)
    monkeypatch.setattr('requests.post', _mock_post_requests)

    # fetching config token before overriding
    config_token = config.get('auth_token')

    if existing_token:
        config.set('auth_token', existing_token)
    else:
        config.delete('auth_token')

    # fetching and deleting env token
    env_token = os.environ.get('JINA_AUTH_TOKEN')
    if env_token:
        del os.environ['JINA_AUTH_TOKEN']

    await Auth.login(force=force)

    authorized_token = config.get('auth_token')
    assert authorized_token == expected_token

    await Auth.logout()
    config.delete('auth_token')

    # putting back config token
    if config_token:
        config.set('auth_token', config_token)

    # putting back env token
    if env_token:
        os.environ['JINA_AUTH_TOKEN'] = env_token


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'existing_token, expected_token, validate_status_code, force',
    [
        ['EXISTING_TOKEN', 'SOME_TOKEN', 200, True],
        ['EXISTING_TOKEN', 'EXISTING_TOKEN', 200, False],
        ['EXISTING_TOKEN', 'SOME_TOKEN', 400, False],
        [None, 'SOME_TOKEN', 200, True],
        [None, 'SOME_TOKEN', 200, False],
    ],
)
async def test_login_logout__sync(
    mocker, monkeypatch, existing_token, expected_token, validate_status_code, force
):
    def _mock_get(*args, **kwargs):
        mock_response = AuthorizeResponseSync(status_code=200)
        return mock_response

    def _mock_post_requests(url, *args, **kwargs):
        if 'user.identity.grant.auto' in url:
            mock_response = GrantResponseSync(status_code=200)
            return mock_response
        if 'user.identity.whoami' in url:
            mock_response = ValidateResponse(status_code=validate_status_code)
            return mock_response

    monkeypatch.setattr('requests.get', _mock_get)
    monkeypatch.setattr('requests.post', _mock_post_requests)

    # fetching config token before overriding
    config_token = config.get('auth_token')

    if existing_token:
        config.set('auth_token', existing_token)
    else:
        config.delete('auth_token')

    # fetching and deleting env token
    env_token = os.environ.get('JINA_AUTH_TOKEN')
    if env_token:
        del os.environ['JINA_AUTH_TOKEN']

    Auth.login_sync(force=force)

    authorized_token = config.get('auth_token')
    assert authorized_token == expected_token

    await Auth.logout()
    config.delete('auth_token')

    # putting back config token
    if config_token:
        config.set('auth_token', config_token)

    # putting back env token
    if env_token:
        os.environ['JINA_AUTH_TOKEN'] = env_token
