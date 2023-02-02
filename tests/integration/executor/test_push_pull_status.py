import os
from pathlib import Path

from hubble import Client
from hubble.executor.hubio import HubIO
from hubble.executor.parsers import (
    set_hub_pull_parser,
    set_hub_push_parser,
    set_hub_status_parser,
)


def test_push_pull_status():
    executor_name = 'IntegrationTestExecutor'
    executor_path = str(
        Path(__file__).parent.parent.parent / 'resources' / 'executor' / executor_name
    )

    c = Client(jsonify=True)

    user = c.get_user_info(variant='data', log_error=False)
    username = user.get('name')

    args = set_hub_push_parser().parse_args(
        [
            '--force',
            executor_name,
            '--build-env',
            'NUMPY_VERSION=1.21.5',
            '--private',
            executor_path,
        ]
    )

    image = HubIO(args).push()
    assert image['name'] == executor_name

    os.environ['NUMPY_VERSION'] = '1.21.5'
    args = set_hub_pull_parser().parse_args(
        [
            '--install-requirements',
            '--force',
            f'jinaai://{username}/{executor_name}:latest',
        ]
    )
    config_path = Path(HubIO(args).pull())

    assert config_path.exists()
    assert config_path.name == 'config.yml'

    args = set_hub_status_parser().parse_args([executor_path])
    HubIO(args).status()
