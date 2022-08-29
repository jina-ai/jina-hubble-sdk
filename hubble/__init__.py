"""
The Hubble Python Client
"""
import asyncio
import os
from functools import wraps
from typing import Optional

from pkg_resources import DistributionNotFound, get_distribution

from .client.client import Client  # noqa F401
from .excepts import AuthenticationRequiredError
from .utils.auth import Auth  # noqa F401

try:
    __version__ = get_distribution("jina-hubble-sdk").version
except DistributionNotFound:
    __version__ = "v0.0.0"


def login_required(func):
    """Annotate a function so that it requires login to Jina AI to run.

    Example:

    .. highlight:: python
    .. code-block:: python

        @login_required
        def foo():
            print(1)

    :param levels: required build level to run this function.
    :return: annotated function
    """

    @wraps(func)
    def arg_wrapper(*args, **kwargs):
        if Client(jsonify=True).token:
            return func(*args, **kwargs)
        else:
            raise AuthenticationRequiredError(
                response={},
                message=f'{func!r} requires login to Jina AI, please do `jina auth login` '
                f'or set env variable `JINA_AUTH_TOKEN`',
            )

    return arg_wrapper


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

    return token


def show_hint(interactive: bool = False) -> Optional[str]:  # noqa: E501
    """
    Show hint if the user is not logged in.

    """
    from rich import print

    c = Client(jsonify=True)

    try:
        print(
            f':closed_lock_with_key: [green bold]You are logged in to Jina AI[/] as [bold]{c.username}[/]. '
            f'To log out, use [dim]jina auth logout[/].'
        )
        return c.token
    except AuthenticationRequiredError:
        print(
            ':closed_lock_with_key: [yellow bold]You are not logged in to Jina AI[/]. '
            'To log in, use [bold]jina auth login[/] or set env variable [bold]JINA_AUTH_TOKEN[/].'
        )
        if interactive:
            from rich.prompt import Confirm

            if Confirm.ask('Do you want to login now?'):
                login()

            return show_hint(interactive=interactive)
    except Exception as ex:
        print(f'Unknown error: {ex}')
