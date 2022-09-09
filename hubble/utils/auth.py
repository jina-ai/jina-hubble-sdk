import json
import os
import webbrowser
from typing import Optional
from urllib.parse import urlencode, urljoin

import aiohttp
from hubble.utils.api_utils import get_base_url
from hubble.utils.config import config
from rich import print


class Auth:
    @staticmethod
    def get_auth_token():
        """Get user auth token.

        .. note:: We first check `JINA_AUTH_TOKEN` environment variable.
          if token is not None, use env token. Otherwise, we get token from config.
        """
        token_from_env = os.environ.get('JINA_AUTH_TOKEN')

        token_from_config: Optional[str] = None
        if isinstance(config.get('auth_token'), str):
            token_from_config = config.get('auth_token')

        return token_from_env if token_from_env else token_from_config

    @staticmethod
    async def login(**kwargs):
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
                            f':point_right: Your browser is going to open the login page. '
                            f'If this fails please open the following link: {item["data"]["redirectTo"]}'
                        )
                        webbrowser.open(item['data']['redirectTo'])
                    elif event == 'authorize':
                        if item['data']['code'] and item['data']['state']:
                            auth_info = item['data']
                        else:
                            print(
                                ':rotating_light: Authentication failed: {}'.format(
                                    item['data']['error_description']
                                )
                            )
                    elif event == 'error':
                        print(
                            ':rotating_light: Authentication failed: {}'.format(
                                item['data']
                            )
                        )
                    else:
                        print(':rotating_light: Unknown event: {}'.format(event))

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
                print(
                    f':closed_lock_with_key: [green]Successfully logged in to Jina AI[/] as [b]{user}[/b]!'
                )

    @staticmethod
    async def logout():
        api_host = get_base_url()

        async with aiohttp.ClientSession(trust_env=True) as session:
            session.headers.update({'Authorization': f'token {Auth.get_auth_token()}'})

            async with session.post(
                url=urljoin(api_host, 'user.session.dismiss')
            ) as response:
                json_response = await response.json()
                if json_response['code'] == 401:
                    print(
                        ':unlock: You are not logged in. There is no need to log out.'
                    )
                elif json_response['code'] == 200:
                    print(':unlock: You have successfully logged out.')
                    config.delete('auth_token')
                else:
                    print(
                        f':rotating_light: Failed to log out. {json_response["message"]}'
                    )
