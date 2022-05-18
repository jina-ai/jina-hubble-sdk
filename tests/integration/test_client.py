import io
import os
import uuid

import pytest
from hubble.client.client import Client

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def client(mocker, request):
    # note this token is set in secrets.
    # to run it locally please replace it with your token.
    mocker.patch(
        'hubble.utils.auth.Auth.get_auth_token',
        return_value=os.environ.get('HUBBLE_ACCESS_TOKEN'),
    )
    return Client(**getattr(request, 'param', {}))


def assert_response(response):
    if not isinstance(response, dict):
        assert response.ok
        response = response.json()

    assert response['code'] == 200


@pytest.mark.parametrize(
    'client', [{'jsonify': True}, {'jsonify': False}], indirect=True
)
def test_create_list_delete_personal_access_token(client):
    pat_name = uuid.uuid4().hex
    resp = client.create_personal_access_token(name=pat_name)
    assert_response(resp)

    resp = client.list_personal_access_tokens()
    assert_response(resp)

    resp = client.delete_personal_access_token(name=pat_name)
    assert_response(resp)


@pytest.mark.parametrize(
    'client', [{'jsonify': True}, {'jsonify': False}], indirect=True
)
def test_get_user_info(client):
    resp = client.get_user_info()
    assert_response(resp)


@pytest.mark.parametrize(
    'client', [{'jsonify': True}, {'jsonify': False}], indirect=True
)
def test_upload_get_delete_artifact(client, tmpdir):
    # upload from path.
    artifact_file = os.path.join(cur_dir, '../resources/model')
    resp = client.upload_artifact(f=artifact_file, show_progress=True)

    assert_response(resp)

    if not client._jsonify:
        resp = resp.json()

    artifact_id1 = resp['data']['_id']

    # upload from bytesio
    resp = client.upload_artifact(
        f=io.BytesIO(b"some initial binary data: \x00\x01"), show_progress=True
    )

    assert_response(resp)

    if not client._jsonify:
        resp = resp.json()

    artifact_id2 = resp['data']['_id']
    resp = client.get_artifact_info(id=artifact_id2)

    assert_response(resp)

    downloaded_artifact = client.download_artifact(
        id=artifact_id2, path=os.path.join(tmpdir, 'model'), show_progress=True
    )
    assert os.path.isfile(downloaded_artifact)

    resp = client.list_artifacts(filter={'metaData.foo': 'bar'}, sort={'type': -1})

    assert_response(resp)

    for artifact_id in [artifact_id1, artifact_id2]:
        resp = client.delete_artifact(id=artifact_id)

        assert_response(resp)
