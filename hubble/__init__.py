"""
The Hubble Python Client
"""
import asyncio
import os
from typing import Optional

from .client.client import Client  # noqa F401
from .excepts import AuthenticationRequiredError
from .utils.auth import Auth  # noqa F401


def login(**kwargs):
    """This function guide user to browser log-in and get token."""
    asyncio.run(Auth.login(**kwargs))


def logout():
    """Logout."""
    asyncio.run(Auth.logout())


def get_token(interactive: bool = False) -> Optional[str]:
    """Get token."""
    if os.environ.get('SHOW_HUBBLE_HINT') == 'ALWAYS':
        token = show_hint(interactive)
    elif os.environ.get('SHOW_HUBBLE_HINT', 'ONCE') == 'ONCE':
        token = show_hint(interactive)
        os.environ['SHOW_HUBBLE_HINT'] = 'NEVER'
    else:
        token = Client(jsonify=True).token

    return os.environ.get('JINA_AUTH_TOKEN', token)


def show_hint(interactive: bool = False) -> Optional[str]:  # noqa: E501
    """
    Show hint if the user is not logged in.

    """
    from rich import print

    c = Client(jsonify=True)

    try:
        print(
            f':closed_lock_with_key: [green bold]You have login to Jina AI[/] as [bold]{c.username}[/]. '
            f'To log out, use [dim]jina auth logout[/].'
        )
        return c.token
    except AuthenticationRequiredError:
        print(
            ':closed_lock_with_key: [yellow bold]You are not login to Jina AI[/]. '
            'To log in, use [bold]jina auth login[/] or set env variable [bold]JINA_AUTH_TOKEN[/].'
        )
        if interactive:
            from rich.prompt import Confirm

            if Confirm.ask('Do you want to login now?'):
                login()

            return show_hint(interactive=interactive)
    except Exception as ex:
        print(f'Unknown error: {ex}')
