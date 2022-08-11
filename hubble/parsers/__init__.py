def get_main_parser():
    """The main parser for Jina
    :return: the parser
    """
    from .base import set_base_parser
    from .helper import _chf
    from .token import set_token_parser

    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(
        dest='cli',
        required=True,
    )

    login_parser = sp.add_parser(
        'login',
        description='Login to Jina AI Ecosystem',
        formatter_class=_chf,
    )

    login_parser.add_argument(
        '-f',
        '--force',
        action='store_true',
        default=False,
        help='Force to login',
    )

    sp.add_parser(
        'logout',
        description='Logout from Jina AI Ecosystem',
        formatter_class=_chf,
    )

    set_token_parser(
        sp.add_parser(
            'token',
            description='Commands for Personal Access Token',
            formatter_class=_chf,
        )
    )

    return parser
