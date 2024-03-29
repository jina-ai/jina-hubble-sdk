import os
from pathlib import Path

import pytest
from hubble.executor import HubExecutor, hubapi

_resource_dir = Path(__file__).parent.parent.parent / 'resources' / 'executor'


@pytest.fixture
def executor_zip_file():
    return _resource_dir / 'dummy_executor.zip'


@pytest.fixture
def test_executor():
    return HubExecutor(uuid='hello', name=None, commit_id='test_commit', tag='v0')


@pytest.mark.parametrize('install_deps', [True, False])
def test_install_local(executor_zip_file, test_executor, install_deps):
    assert not hubapi.exist_local(test_executor.uuid, test_executor.tag)
    hubapi.install_local(executor_zip_file, test_executor, install_deps=install_deps)
    assert hubapi.exist_local(test_executor.uuid, test_executor.tag)
    assert any(
        str(path).endswith(
            f'{os.path.join(test_executor.uuid, test_executor.tag)}.dist-info'
        )
        for path in hubapi.list_local()
    )

    hubapi.uninstall_local(test_executor.uuid)
    assert not hubapi.exist_local(test_executor.uuid, test_executor.tag)


@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('name', ['dummy_executor'])
def test_load_config(mocker, path, name):
    exec_path = _resource_dir / path
    config = hubapi.load_config(exec_path)

    assert config['jtype'] == name
