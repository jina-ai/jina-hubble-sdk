import json
import os
import webbrowser
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

import aiohttp
from hubble.utils.config import config


@lru_cache()
def _get_cloud_api_url() -> str:
    """Get Cloud Api for transmiting data to the cloud.

    :raises RuntimeError: Encounter error when fetching the cloud Api Url.
    :return: Cloud Api Url
    """
    if 'JINA_HUBBLE_REGISTRY' in os.environ:
        return os.environ['JINA_HUBBLE_REGISTRY']
    else:
        try:
            req = Request(
                'https://api.jina.ai/hub/hubble.json',
                headers={'User-Agent': 'Mozilla/5.0'},
            )
            with urlopen(req) as resp:
                return json.load(resp)['url']
        except Exception as ex:
            raise ex


class Auth:
    @staticmethod
    def get_auth_token():
        return config.get('auth_token')

    @staticmethod
    async def login():
        api_host = _get_cloud_api_url()

        async with aiohttp.ClientSession() as session:
            redirect_url = 'http://localhost:8085'

            async with session.get(
                url=f'{api_host}/v2/rpc/user.identity.authorize?'
                f'provider=jina-login&redirectUri={redirect_url}'
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                webbrowser.open(json_response['data']['redirectTo'], new=2)

        done = False
        post_data = None

        class S(BaseHTTPRequestHandler):
            def _set_response(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

            def do_POST(self):
                nonlocal done, post_data

                content_length = int(self.headers['Content-Length'])
                post_data = parse_qs(self.rfile.read(content_length))

                self._set_response()
                self.wfile.write(
                    'You have successfully logged in!'
                    'You can close this window now.'.encode('utf-8')
                )
                done = True

            def log_message(self, format, *args):
                return

        server_address = ('', 8085)
        with HTTPServer(server_address, S) as httpd:
            while not done:
                httpd.handle_request()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f'{api_host}/v2/rpc/user.identity.grant.auth0Unified',
                data=post_data,
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                token = json_response['data']['token']

                config.set('auth_token', token)
                print('🔐 Successfully login to Jina Ecosystem!')

    @staticmethod
    async def logout():
        api_host = _get_cloud_api_url()

        async with aiohttp.ClientSession() as session:
            session.headers.update({'Authorization': f'token {Auth.get_auth_token()}'})

            async with session.post(
                url=f'{api_host}/v2/rpc/user.session.dismiss',
            ) as response:
                json_response = await response.json()
                if json_response['code'] == 401:
                    print('🔓 You are not logged in. No need to logout.')
                elif json_response['code'] == 200:
                    print('🔓 You have successfully logged out.')
                    config.delete('auth_token')
                else:
                    print(f'🚨 Failed to logout. {json_response["message"]}')
