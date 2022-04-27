import os
import uuid

import pytest
from hubble.client.client import Client

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def client(mocker):
    # note this token is set in secrets.
    # to run it locally please replace it with your token.
    mocker.patch(
        'hubble.utils.auth.Auth.get_auth_token',
        return_value=os.environ.get('HUBBLE_ACCESS_TOKEN'),
    )
    return Client()


def test_create_list_delete_personal_access_token(client):
    pat_name = uuid.uuid4().hex
    resp = client.create_personal_access_token(name=pat_name)
    assert resp.ok
    resp = client.list_personal_access_tokens()
    assert resp.ok
    resp = client.delete_personal_access_token(name=pat_name)
    assert resp.ok


def test_get_user_info(client):
    resp = client.get_user_info()
    assert resp.ok


def test_upload_get_delete_artifact(client, tmpdir):
    artifact_dir = os.path.join(cur_dir, '../resources/model')
    resp = client.upload_artifact(path=artifact_dir)
    assert resp.ok
    artifact_id = resp.json()['data']['_id']
    resp = client.get_artifact_info(id=artifact_id)
    assert resp.ok
    downloaded_artifact = client.download_artifact(
        id=artifact_id, path=os.path.join(tmpdir, 'model')
    )
    assert os.path.isfile(downloaded_artifact)
    resp = client.delete_artifact(id=artifact_id)
    assert resp.ok
