def main():
    from .parsers import get_main_parser

    args = get_main_parser().parse_args()

    try:
        from . import api

        getattr(api, args.cli2.replace('-', '_'))(args)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
