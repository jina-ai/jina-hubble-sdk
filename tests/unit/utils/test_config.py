import pytest
import os
from pathlib import Path
from hubble.utils.config import Config, CONFIG_FILE_NAME, ROOT_ENV_NAME

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