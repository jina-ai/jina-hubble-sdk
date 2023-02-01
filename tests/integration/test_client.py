import io
import os
import uuid

import pytest
from hubble.client.client import Client
from hubble.excepts import (
    IdentifierNamespaceOccupiedError,
    OperationNotAllowedError,
    RequestedEntityNotFoundError,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def client(request):
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
    user = client.get_user_info()
    assert isinstance(user, dict)
    assert type(user['_id']) is str


@pytest.mark.parametrize(
    'client', [{'jsonify': True}, {'jsonify': False}], indirect=True
)
def test_get_raw_session(client):
    resp = client.get_raw_session()
    assert_response(resp)


@pytest.mark.parametrize(
    'client', [{'jsonify': True}, {'jsonify': False}], indirect=True
)
def test_upload_get_delete_artifact(client, tmpdir):
    # upload from path.
    artifact_file = os.path.join(cur_dir, '../resources/model')
    resp = client.upload_artifact(
        f=artifact_file, show_progress=True, name='my-artifact'
    )

    assert_response(resp)

    if not client._jsonify:
        resp = resp.json()

    data = resp['data']
    artifact_id1 = data['_id']

    assert data['visibility'] == 'private'
    assert data.get('metaData', None) is None
    assert data['name'] == 'my-artifact'

    resp = client.update_artifact(
        id=artifact_id1, is_public=True, metadata={'a': 1}, name='my-artifact'
    )
    if not client._jsonify:
        resp = resp.json()

    data = resp['data']

    assert data['visibility'] == 'public'
    assert data['metaData'] == {'a': 1}
    assert data['name'] == 'my-artifact'

    # upload from bytesio
    resp = client.upload_artifact(
        f=io.BytesIO(b"some initial binary data: \x00\x01"),
        show_progress=True,
    )

    assert_response(resp)

    if not client._jsonify:
        resp = resp.json()

    artifact_id2 = resp['data']['_id']
    resp = client.get_artifact_info(id=artifact_id2)

    assert_response(resp)

    downloaded_artifact = client.download_artifact(
        id=artifact_id2, f=os.path.join(tmpdir, 'model'), show_progress=True
    )
    assert os.path.isfile(downloaded_artifact)

    resp = client.list_artifacts(filter={'metaData.foo': 'bar'}, sort={'type': -1})

    assert_response(resp)

    for artifact_id in [artifact_id1, artifact_id2]:
        resp = client.delete_artifact(id=artifact_id)

        assert_response(resp)


@pytest.mark.parametrize('client', [{'jsonify': True}], indirect=True)
def test_delete_multiple_artifacts(client: Client):
    file_path = os.path.join(cur_dir, '../resources/model')

    ids = [
        resp['data']['_id']
        for resp in [
            client.upload_artifact(f=file_path),
            client.upload_artifact(f=file_path),
            client.upload_artifact(f=file_path),
            client.upload_artifact(f=file_path),
        ]
    ]

    names = ['delete_multiple_artifacts_1', 'delete_multiple_artifacts_2']
    for name in names:
        try:
            client.update_artifact(id=ids[0], name=name)
            ids.pop(0)
        except IdentifierNamespaceOccupiedError:
            pass

    resp = client.get_artifact_info(id=ids[0])
    assert_response(resp)

    resp = client.get_artifact_info(name=names[0])
    assert_response(resp)

    resp = client.delete_multiple_artifacts(ids=ids, names=names)
    assert_response(resp)

    with pytest.raises(RequestedEntityNotFoundError):
        client.get_artifact_info(id=ids[0])

    with pytest.raises((RequestedEntityNotFoundError, OperationNotAllowedError)):
        client.get_artifact_info(name=names[0])


def test_upload_download_artifact_bytes(client):
    # upload from path.
    data = b'some initial binary data: \x00\x01'
    resp = client.upload_artifact(f=io.BytesIO(data), show_progress=True)
    assert_response(resp)

    if not client._jsonify:
        resp = resp.json()

    artifact_id1 = resp['data']['_id']

    # download as buffer
    obj = io.BytesIO()
    resp = client.download_artifact(artifact_id1, f=obj)
    assert isinstance(resp, io.BytesIO)
    resp.seek(0)
    assert resp.read() == data

    resp = client.delete_artifact(id=artifact_id1)
    assert_response(resp)


@pytest.mark.parametrize(
    'client', [{'jsonify': True}, {'jsonify': False}], indirect=True
)
def test_list_internal_docker_registries(client):
    resp = client.list_internal_docker_registries()
    assert_response(resp)

    if not client._jsonify:
        resp = resp.json()

    registries = resp['data']

    assert type(registries[0]) is str
