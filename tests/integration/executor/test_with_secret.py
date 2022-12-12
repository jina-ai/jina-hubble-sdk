from pathlib import Path

from hubble.executor.hubio import HubIO
from hubble.executor.parsers import set_hub_pull_parser, set_hub_push_parser


def test_legacy_pull_push_with_secret():
    executor_name = 'SanityCheck'
    executor_secret = 'sanity@Check'

    args = set_hub_pull_parser().parse_args(
        ['--force', f'jinahub://{executor_name}:{executor_secret}/latest']
    )
    config_path = Path(HubIO(args).pull())

    assert config_path.exists()
    assert config_path.name == 'config.yml'

    args = set_hub_push_parser().parse_args(
        [
            '--force',
            executor_name,
            '--secret',
            executor_secret,
            '--private',
            str(config_path.parent),
        ]
    )

    image = HubIO(args).push()
    assert image['name'] == executor_name
    assert image['secret'] == executor_secret
