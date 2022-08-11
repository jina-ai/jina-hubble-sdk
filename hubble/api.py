import os

from . import Client
from . import login as _login
from .excepts import AuthenticationFailedError, AuthenticationRequiredError


def login(args):
    client = Client(max_retries=None)

    from rich.console import Console

    console = Console()

    if args.force:
        _login(prompt='login')
        return

    try:
        nickname = client.username
        if nickname:
            console.print(
                f'You are already logged in as [b green]{nickname}[/b green].',
                '',
                'If you want to login to another account, please do either:',
                '- run [b]jina auth logout[/]',
                '- or run [b]jina auth login -f[/]',
                sep=os.linesep,
            )
    except Exception as ex:
        if isinstance(ex, (AuthenticationRequiredError, AuthenticationFailedError)):
            _login(prompt='login')
        else:
            raise ex


def token(args):
    client = Client(max_retries=None)

    if args.operation == 'create':
        response = client.create_personal_access_token(
            name=args.name, expiration_days=args.expire
        )

        response.raise_for_status()
        token = response.json()['data']['token']

        import rich
        from rich.panel import Panel

        rich.print(
            Panel(
                f'token: [b]{token}[/b]',
                title=':party_popper: [green]Successfully created',
                subtitle=':point_up:️ [red]Please keep this token in a safe place!',
                width=50,
            )
        )

    if args.operation == 'delete':
        response = client.delete_personal_access_token(name=args.name)

        response.raise_for_status()

        import rich
        from rich.panel import Panel

        rich.print(
            Panel(
                f'[b]{args.name}[/b]',
                title=':party_popper: [green]Successfully deleted',
                width=50,
            )
        )

    if args.operation == 'list':
        response = client.list_personal_access_tokens()
        response.raise_for_status()
        tokens = response.json()['data']['personal_access_tokens']

        import rich
        from rich.table import Table

        table = Table(title="Your personal access tokens")
        table.add_column("ID", justify="center", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Name", justify="center", style="green")
        table.add_column("ExpireAt", justify="center", style="green")
        table.add_column("CreatedAt", justify="center", style="green")
        table.add_column("UpdatedAt", justify="center", style="green")

        for token in tokens:
            table.add_row(
                token['_id'],
                token['type'],
                token['name'],
                token['expireAt'],
                token['createdAt'],
                token['updatedAt'],
            )

        rich.print(table)
