"""Argparser module for hub list"""
import os

from hubble.parsers.helper import add_arg_group


def mixin_hub_list_parser(parser):
    """Add the arguments for hub list to the parser
    :param parser: the parser configure
    """

    add_arg_group(parser, title='List')
