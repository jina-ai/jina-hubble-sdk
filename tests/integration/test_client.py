import os
import uuid

import pytest
from hubble.client.client import Client

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def client():
    token = os.environ.get('HUBBLE_ACCESS_TOKEN')
    if not token:
        raise ValueError(
            'Please set `Hubble_ACCESS_TOKEN` before starting integration test'
        )
    return Client(api_token=token)


def test_create_list_delete_personal_access_token(client):
    pat_name = uuid.uuid4().hex
    resp = client.create_personal_access_token(name=pat_name)
    assert resp.ok
    resp = client.list_personal_access_tokens()
    assert resp.ok
    pat_id = resp.json()['data']['personal_access_tokens'][0]['_id']
    resp = client.delete_personal_access_token(personal_access_token_id=pat_id)
    assert resp.ok


def test_get_user_info(client):
    resp = client.get_user_info()
    assert resp.ok


def test_upload_get_delete_artifact(client):
    artifact_dir = os.path.join(cur_dir, '../resources/model')
    resp = client.upload_artifact(path=artifact_dir)
    assert resp.ok
    artifact_id = resp.json()['data']['_id']
    resp = client.get_artifact_info(id=artifact_id)
    assert resp.ok
    resp = client.delete_artifact(id=artifact_id)
    assert resp.ok
