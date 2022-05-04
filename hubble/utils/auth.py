import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

import aiohttp
from hubble.utils.api_utils import get_base_url
from hubble.utils.config import config
from requests.compat import urljoin


class Auth:
    @staticmethod
    def get_auth_token():
        """Get user auth token.

        .. note:: We first check `JINA_AUTH_TOKEN` environment variable.
          if token is not None, use env token. Otherwise, we get token from config.
        """
        token_from_env = os.environ.get('JINA_AUTH_TOKEN')
        return token_from_env if token_from_env else config.get('auth_token')

    @staticmethod
    async def login():
        api_host = get_base_url()

        async with aiohttp.ClientSession() as session:
            redirect_url = 'http://localhost:8085'

            async with session.get(
                url=urljoin(
                    api_host,
                    'user.identity.authorize?provider=jina-login&redirectUri=',
                )
                + redirect_url
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
                url=urljoin(api_host, 'user.identity.grant.auth0Unified'),
                data=post_data,
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                token = json_response['data']['token']

                config.set('auth_token', token)
                print('🔐 Successfully login to Jina Ecosystem!')

    @staticmethod
    async def logout():
        api_host = get_base_url()

        async with aiohttp.ClientSession() as session:
            session.headers.update({'Authorization': f'token {Auth.get_auth_token()}'})

            async with session.post(
                url=urljoin(api_host, 'user.session.dismiss')
            ) as response:
                json_response = await response.json()
                if json_response['code'] == 401:
                    print('🔓 You are not logged in. No need to logout.')
                elif json_response['code'] == 200:
                    print('🔓 You have successfully logged out.')
                    config.delete('auth_token')
                else:
                    print(f'🚨 Failed to logout. {json_response["message"]}')
