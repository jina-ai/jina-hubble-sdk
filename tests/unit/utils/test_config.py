import os
from pathlib import Path

import pytest
from hubble.utils import auth
from hubble.utils.config import CONFIG_FILE_NAME, ROOT_ENV_NAME, Config


@pytest.fixture
def config_path():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return Path(os.path.join(dir_path, CONFIG_FILE_NAME))


@pytest.fixture
def config():
    os.environ[ROOT_ENV_NAME] = os.path.dirname(os.path.realpath(__file__))
    return Config(config_file_name=CONFIG_FILE_NAME, root_env_name=ROOT_ENV_NAME)


def test_config(config, config_path):
    config.set('test', 'test')
    assert config.get('test') == 'test'

    config.delete('test')
    assert config.get('test') is None

    assert config_path.exists()
    config.purge()
    assert not config_path.exists()


def test_get_auth_token(config, config_path):
    auth.config = config
    config.set('auth_token', 'my-token')
    assert config.get('auth_token') == 'my-token'
    assert auth.Auth.get_auth_token() == 'my-token'

    os.environ['JINA_AUTH_TOKEN'] = 'my-token-from-env'
    assert config.get('auth_token') == 'my-token'
    assert auth.Auth.get_auth_token() == 'my-token-from-env'
