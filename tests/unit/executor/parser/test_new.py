import argparse

from hubble.executor.parsers.new import mixin_hub_new_parser


def test_new_parser():
    parser = argparse.ArgumentParser(
        epilog='Test', description='Test Hub Command Line Interface'
    )

    mixin_hub_new_parser(parser)

    args = parser.parse_args([])
    assert not args.dockerfile
    assert not args.advance_configuration
    assert args.name is None
    assert args.path is None
    assert args.description is None
    assert args.keywords is None
    assert args.url is None

    args = parser.parse_args(['--dockerfile', 'cpu'])
    assert args.dockerfile

    args = parser.parse_args(['--advance-configuration'])
    assert args.advance_configuration

    args = parser.parse_args(
        [
            '--name',
            'Dummy Executor',
            '--path',
            'Dummy Path',
            '--description',
            'Dummy description',
            '--keywords',
            'Dummy keywords',
            '--url',
            'Dummy url',
        ]
    )
    assert not args.dockerfile
    assert not args.advance_configuration
    assert args.name == 'Dummy Executor'
    assert args.path == 'Dummy Path'
    assert args.description == 'Dummy description'
    assert args.keywords == 'Dummy keywords'
    assert args.url == 'Dummy url'

    args = parser.parse_args(
        [
            '--name',
            'Dummy Executor',
            '--path',
            'Dummy Path',
            '--description',
            'Dummy description',
            '--keywords',
            'Dummy keywords',
            '--url',
            'Dummy url',
            '--advance-configuration',
        ]
    )
    assert not args.dockerfile
    assert args.advance_configuration
    assert args.name == 'Dummy Executor'
    assert args.path == 'Dummy Path'
    assert args.description == 'Dummy description'
    assert args.keywords == 'Dummy keywords'
    assert args.url == 'Dummy url'

    args = parser.parse_args(
        [
            '--dockerfile',
            'cpu',
            '--name',
            'Dummy Executor',
            '--path',
            'Dummy Path',
            '--description',
            'Dummy description',
            '--keywords',
            'Dummy keywords',
            '--url',
            'Dummy url',
        ]
    )
    assert args.dockerfile
    assert not args.advance_configuration
    assert args.name == 'Dummy Executor'
    assert args.path == 'Dummy Path'
    assert args.description == 'Dummy description'
    assert args.keywords == 'Dummy keywords'
    assert args.url == 'Dummy url'
