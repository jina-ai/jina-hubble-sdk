import os
from pathlib import Path

import pytest
from hubble.executor import HubExecutor, hubapi

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def executor_zip_file():
    return Path(__file__).parent / 'dummy_executor.zip'


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


def test_load_dump_secret():
    import tempfile

    uuid8 = 'hello'
    secret = 'world'
    task_id = 'UUID'
    with tempfile.TemporaryDirectory() as tmp_dirname:
        hubapi.dump_secret(Path(tmp_dirname), uuid8, secret, task_id)
        new_uuid8, new_secret, new_task_id = hubapi.load_secret(Path(tmp_dirname))
    assert new_uuid8 == uuid8
    assert new_secret == secret
    assert task_id == new_task_id


def test_load_dump_secret_existing_encryption_key():
    import tempfile

    uuid8 = 'hello'
    secret = 'world'
    task_id = 'UUID'
    with tempfile.TemporaryDirectory() as tmp_dirname:
        # creates an encryption key
        hubapi.dump_secret(Path(tmp_dirname), 'dummy', 'dummy', 'dummy')

        # dump secret using existing encryption key
        hubapi.dump_secret(Path(tmp_dirname), uuid8, secret, task_id)
        new_uuid8, new_secret, new_task_id = hubapi.load_secret(Path(tmp_dirname))
    assert new_uuid8 == uuid8
    assert new_secret == secret
    assert task_id == new_task_id


@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('name', ['dummy_executor'])
def test_load_config(mocker, path, name):
    exec_path = os.path.join(cur_dir, path)
    config = hubapi.load_config(Path(exec_path))

    assert config['jtype'] == name
