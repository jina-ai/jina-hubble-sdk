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
    from rich.panel import Panel

    c = Client(jsonify=True)

    try:
        print(
            Panel(
                f'''You have logged into Jina AI as [green bold]{c.username}[/], which gives you a lot of benefits:
- You can easily manage the DocumentArray, Executor, Flow via the web console.
- You enjoy persist DocumentArray with [b]unlimited-time, privately[/] .
- More features are coming soon.

:unlock: To log out, use [dim]jina auth logout[/].''',
                title=':sunglasses: [green bold]You have logged in[/]',
                width=50,
            )
        )
        return c.token
    except AuthenticationRequiredError:
        print(
            Panel(
                f'''Jina AI offers many free benefits for logged in users.
- Easily manage the DocumentArray, Executor, Flow via the web console.
- Persist DocumentArray with [b]unlimited-time, privately[/] .
- More features are coming soon.

{':closed_lock_with_key: To log in, use [bold]jina auth login[/].' if not interactive else ''}''',
                title=':no_mouth: [yellow bold]You are not logged in[/]',
                width=50,
            )
        )
        if interactive:
            from rich.prompt import Confirm

            if Confirm.ask('Do you want to login now?'):
                login()

            return show_hint(interactive=interactive)
    except Exception as ex:
        print(f'Unknown error: {ex}')
