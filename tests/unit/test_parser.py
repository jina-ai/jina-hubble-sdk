from argparse import ArgumentParser

import pytest
from hubble.parsers import get_main_parser


@pytest.fixture
def parser() -> "ArgumentParser":
    return get_main_parser()


@pytest.mark.parametrize(
    'input,expected',
    [
        (['login'], ['login', False]),
        (['login', '-f'], ['login', True]),
    ],
)
def test_login(parser: 'ArgumentParser', input, expected):
    assert parser.parse_args(input).cli2 == expected[0]
    assert parser.parse_args(input).force == expected[1]


@pytest.mark.parametrize(
    'input,expected',
    [
        (['logout'], ['logout']),
    ],
)
def test_logout(parser: 'ArgumentParser', input, expected):
    assert parser.parse_args(input).cli2 == expected[0]


@pytest.mark.parametrize(
    'input,expected',
    [
        (['token', 'create', 'foo'], ['token', 'create', 7, 'foo']),
        (['token', 'create', '-e', '10', 'foo'], ['token', 'create', 10, 'foo']),
        (['token', 'create', '--expire', '10', 'foo'], ['token', 'create', 10, 'foo']),
    ],
)
def test_token_create(parser: 'ArgumentParser', input, expected):
    assert parser.parse_args(input).cli2 == expected[0]
    assert parser.parse_args(input).operation == expected[1]
    assert parser.parse_args(input).expire == expected[2]
    assert parser.parse_args(input).name == expected[3]


@pytest.mark.parametrize(
    'input,expected',
    [
        (['token', 'delete', 'foo'], ['token', 'delete', 'foo']),
    ],
)
def test_token_delete(parser: 'ArgumentParser', input, expected):
    assert parser.parse_args(input).cli2 == expected[0]
    assert parser.parse_args(input).operation == expected[1]
    assert parser.parse_args(input).name == expected[2]
