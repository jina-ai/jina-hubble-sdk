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
from hubble.excepts import AuthenticationFailedError
from rich import print as rich_print


JINA_LOGO = 'https://d2vchdhjlcm3i6.cloudfront.net/Company+Logo/Light/Company+logo_light.svg'

NOTEBOOK_LOGIN_HTML = f"""
<center>
    <img src={JINA_LOGO} width=175 alt="Jina AI">
    <p><br></p>
    <p> 
        Copy a <b>Personal Access Token</b>, paste it below, and press the Login button.
        <br>
        If you do not have a token, press the Login button to login via the browser.
    </p>
</center>
"""

NOTEBOOK_LOGGED_IN_HTML = f"""
<center>
    <img src={JINA_LOGO} width=175 alt="Jina AI">
    <p><br></p>
    <p>
        You are logged to Jina AI!
    </p>
</center>
"""

NOTEBOOK_LOGIN_REDIRECT_HTML = """
<center>
    <img src={LOGO} width=175 alt="Jina AI">
    <p>
        Please open the following <a href='{HREF}' target='_blank'>link</a> to continue the login process.
    </p>
</center>
"""


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
    def validate_token(token):
        try:
            session = HubbleAPISession()
            session.init_jwt_auth(token)
            resp = session.validate_token()
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            raise AuthenticationFailedError("Could not validate token")


    # TODO: refactor this function to first check if there is an existing token and then construct widgets
    @staticmethod
    def login_notebook(**kwargs):
        """Login user in notebook environments like colab"""

        # trying to import utilities (only available in notebook env)
        try:
            import ipywidgets.widgets as widgets
            from IPython.display import clear_output, display
        except ImportError:
            raise ImportError(
                """
The `notebook_login` function can only be used in a notebook.
The function also requires `ipywidgets`.
                """
            )

        # creating widgets

        layout = widgets.Layout(
            display="flex", flex_flow="column", align_items="center"
        )    

        token_widget = widgets.Password(placeholder="Personal Access Token (PAT)", layer=widgets.Layout(width="300px"))
        button_widget = widgets.Button(description="Login", layout=widgets.Layout(width="300px"))
        login_widget = widgets.VBox(
            [
                widgets.HTML(NOTEBOOK_LOGIN_HTML),
                token_widget,
                button_widget
            ],
            layout=layout,
        )

        loggedin_widget = widgets.VBox(
            [
                widgets.HTML(NOTEBOOK_LOGGED_IN_HTML)
            ],
            layout=layout
        )

        redirect_url_widget = widgets.HTML(value="")
        redirect_widget = widgets.VBox(
            [
                redirect_url_widget, 
            ],
            layout=layout
        )

        def _login(*args):

            # reading token and clearing form
            token = token_widget.value
            token_widget.value = ""

            # set token as auth token
            if token != "":
                config.set('auth_token', token)

            # verifying existing toiken
            token = Auth.get_auth_token()
            if token:
                try:
                    Auth.validate_token(token)
                    # clearing output and displaying success
                    clear_output()
                    display(loggedin_widget)
                    return
                except AuthenticationFailedError:
                    pass

            api_host = get_base_url()
            auth_info = None

            # authorize user
            url=urljoin(api_host, 'user.identity.proxiedAuthorize?{}'.format(urlencode({'provider': 'jina-login'})))   
            session = requests.Session()
            response = session.get(url, stream=True)

            # iterate through response
            for line in response.iter_lines():

                item = json.loads(line.decode('utf-8'))
                event = item['event']

                # TODO: better error message
                if event == 'redirect':
                    # f'Please open the following link {item["data"]["redirectTo"]}'
                    print('should redirect')
                    redirect_url_widget.value = NOTEBOOK_LOGIN_REDIRECT_HTML.format(LOGO=JINA_LOGO, HREF=item['data']["redirectTo"])
                    clear_output()
                    display(redirect_url_widget)
                elif event == 'authorize':
                    if item['data']['code'] and item['data']['state']:
                        auth_info = item['data']
                    else:
                        print(f'Authentication failed: {item["data"]["error_description"]}')
                elif event == 'error':
                    print(f'Authentication failed: {item["data"]}')
                else:
                    print(f'Unknown event: {event}')

            session.close()

            # FIXME: show error message here 
            if auth_info is None:
                return

            # retrieving token
            url=urljoin(api_host, 'user.identity.grant.auto')
            response = requests.post(url, json=auth_info)
            response.raise_for_status()
            json_response = response.json()
            token = json_response['data']['token']
            user = json_response['data']['user']['nickname']

            config.set('auth_token', token)

            # FIXME: do we need docker auth ?
            from hubble.dockerauth import (
                auto_deploy_hubble_docker_credential_helper,
            )

            auto_deploy_hubble_docker_credential_helper()

            clear_output()
            display(loggedin_widget)

        button_widget.on_click(_login)

        display(login_widget)


    @staticmethod
    async def login(force=False, **kwargs):
        # verify if token already exists, authenticate token if exists
        if not force:
            token = Auth.get_auth_token()
            if token:
                try:
                    Auth.validate_token(token)
                    return
                except AuthenticationFailedError:
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
