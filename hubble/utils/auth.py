import json
import os
import webbrowser
from typing import Optional
from urllib.parse import urlencode, urljoin

import aiohttp
import requests
from hubble.client.session import HubbleAPISession
from hubble.utils.api_utils import get_base_url
from hubble.utils.config import config
from rich import print as rich_print


class Auth:
    @staticmethod
    def get_auth_token_from_config():
        """Get user auth token from config file."""
        token_from_config: Optional[str] = None
        if isinstance(config.get('auth_token'), str):
            token_from_config = config.get('auth_token')

        return token_from_config

    @staticmethod
    def get_auth_token():
        """Get user auth token.

        .. note:: We first check `JINA_AUTH_TOKEN` environment variable.
          if token is not None, use env token. Otherwise, we get token from config.
        """
        token_from_env = os.environ.get('JINA_AUTH_TOKEN')

        token_from_config: Optional[str] = Auth.get_auth_token_from_config()

        return token_from_env if token_from_env else token_from_config

    @staticmethod
    async def login(force=False, **kwargs):
        # verify if token already exists, authenticate token if exists
        if not force:
            token = Auth.get_auth_token()
            if token:
                session = HubbleAPISession()
                session.init_jwt_auth(token)
                try:
                    resp = session.validate_token()
                    resp.raise_for_status()
                    return
                except requests.exceptions.HTTPError:
                    pass

        api_host = get_base_url()
        auth_info = None
        async with aiohttp.ClientSession(trust_env=True) as session:
            kwargs['provider'] = kwargs.get('provider', 'jina-login')

            async with session.get(
                url=urljoin(
                    api_host,
                    'user.identity.proxiedAuthorize?{}'.format(urlencode(kwargs)),
                ),
            ) as response:
                async for line in response.content:
                    item = json.loads(line.decode('utf-8'))
                    event = item['event']
                    if event == 'redirect':
                        print(
                            f'Your browser is going to open the login page.\n'
                            f'If this fails please open the following link: {item["data"]["redirectTo"]}'
                        )
                        webbrowser.open(item['data']['redirectTo'])
                    elif event == 'authorize':
                        if item['data']['code'] and item['data']['state']:
                            auth_info = item['data']
                        else:
                            rich_print(
                                ':rotating_light: Authentication failed: {}'.format(
                                    item['data']['error_description']
                                )
                            )
                    elif event == 'error':
                        rich_print(
                            ':rotating_light: Authentication failed: {}'.format(
                                item['data']
                            )
                        )
                    else:
                        rich_print(':rotating_light: Unknown event: {}'.format(event))

        if auth_info is None:
            return

        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.post(
                url=urljoin(api_host, 'user.identity.grant.auto'),
                data=auth_info,
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                token = json_response['data']['token']
                user = json_response['data']['user']['nickname']

                config.set('auth_token', token)

                from hubble.dockerauth import (
                    auto_deploy_hubble_docker_credential_helper,
                )

                auto_deploy_hubble_docker_credential_helper()

                rich_print(
                    f':closed_lock_with_key: [green]Successfully logged in to Jina AI[/] as [b]{user}[/b]!'
                )

    @staticmethod
    async def logout():
        api_host = get_base_url()

        token = Auth.get_auth_token()
        token_from_config = Auth.get_auth_token_from_config()
        if token != token_from_config:
            rich_print(':warning: The token from environment variable is ignored.')

        async with aiohttp.ClientSession(trust_env=True) as session:
            session.headers.update({'Authorization': f'token {token_from_config}'})

            async with session.post(
                url=urljoin(api_host, 'user.session.dismiss')
            ) as response:
                json_response = await response.json()
                if json_response['code'] == 401:
                    rich_print(
                        ':unlock: You are not logged in locally. There is no need to log out.'
                    )
                elif json_response['code'] == 200:
                    rich_print(':unlock: You have successfully logged out.')
                    config.delete('auth_token')
                else:
                    rich_print(
                        f':rotating_light: Failed to log out. {json_response["message"]}'
                    )
