"""
The Hubble Python Client
"""
import asyncio
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
                f'''You are logged into Jina AI as [green bold]{c.username}[/], which gives you a lot of benefits:
- You can easily manage the DocumentArray, Executor, Flow via the web Console.
- You enjoy [b]unlimited-time, protected[/] storage for the DocumentArray.
- More features are coming soon.

:unlock: To log out, use [dim]jina auth logout[/].''',
                title=':sunglasses: [green bold]You are logged in[/]',
                width=50,
            )
        )
        return c.token
    except AuthenticationRequiredError:
        print(
            Panel(
                f'''Jina AI offers many free benefits for logged in users.
- They can easily manage the DocumentArray, Executor, Flow via the web Console.
- They enjoy [b]unlimited-time, protected[/] storage for the DocumentArray.
- More features are coming soon for them.

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
