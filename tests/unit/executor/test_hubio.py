import cgi
import itertools
import json
import os
import urllib
from argparse import Namespace
from io import BytesIO
from pathlib import Path

import docker
import hubble
import pytest
import requests
import yaml
from hubble.executor import hubio
from hubble.executor.helper import disk_cache_offline, get_requirements_env_variables
from hubble.executor.hubio import HubExecutor, HubIO
from hubble.executor.parsers import (
    set_hub_list_parser,
    set_hub_new_parser,
    set_hub_pull_parser,
    set_hub_push_parser,
    set_hub_status_parser,
)
from hubble.utils.api_utils import get_base_url

_resource_dir = Path(__file__).parent.parent.parent / 'resources' / 'executor'


class PostMockResponse:
    def __init__(self, response_code: int = 201, response_error: str = ''):
        self.response_code = response_code
        self.response_error = response_error

    def json(self):
        return {
            'type': 'complete',
            'subject': 'createExecutor',
            'message': 'Successfully pushed w7qckiqy',
            'payload': {
                'id': 'w7qckiqy',
                'secret': 'f7386f9ef7ea238fd955f2de9fb254a0',
                'visibility': 'public',
            },
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code

    def iter_lines(self):
        logs = [
            '{"type":"init","subject":"createExecutor"}',
            '{"type":"start","subject":"extractZip"}',
            '{"type":"done","subject":"extractZip"}',
            '{"type":"start","subject":"pushImage"}',
            '{"type":"done","subject":"pushImage"}',
            '{"type":"progress","subject":"buildWorkspace"}',
            '{"type":"console","subject":"pushImage","payload":"payload_test"}',
            (
                b'{"type":"complete","subject":"createExecutor","message":"Successfully pushed w7qckiqy",'
                b'"payload": {"id":"w7qckiqy","secret":"f7386f9ef7ea238fd955f2de9fb254a0","visibility":"public"}}'
            ),
        ]

        if self.response_error == 'response_error':
            logs = [
                b'{"type":"error","message":"test error", "payload":{"readableMessage": "readableMessage"}}',
                '{"type":"start","subject":"extractZip"}',
                '{"type":"done","subject":"extractZip"}',
                '{"type":"start","subject":"pushImage"}',
                '{"type":"done","subject":"pushImage"}',
                '{"type":"console","subject":"pushImage","payload":"payload_test"}',
                (
                    b'{"type":"complete","subject":"createExecutor","message":"Successfully pushed w7qckiqy",'
                    b'"payload":{"id":"w7qckiqy","secret":"f7386f9ef7ea238fd955f2de9fb254a0","visibility":"public"}}'
                ),
            ]

        if self.response_error == 'image_not_exits':
            logs = [
                '{"type":"error","message":"test error"}',
                '{"type":"start","subject":"extractZip"}',
                '{"type":"done","subject":"extractZip"}',
                '{"type":"start","subject":"pushImage"}',
                '{"type":"done","subject":"pushImage"}',
                '{"type":"console","subject":"pushImage","payload":"payload_test"}',
                b'{"type":"complete","subject":"createExecutor","message":"Successfully pushed w7qckiqy"}',
            ]

        return itertools.chain(logs)


class FetchMetaMockResponse:
    def __init__(
        self,
        response_code: int = 200,
        no_image=False,
        fail_count=0,
        add_build_env=False,
    ):
        self.response_code = response_code
        self.no_image = no_image
        self._tried_count = 0
        self._fail_count = fail_count
        self._build_env = add_build_env

    def json(self):
        if self._tried_count <= self._fail_count:
            return {'message': 'Internal server error'}

        commit_val = {'_id': 'commit_id', 'tags': ['v0']}
        if self._build_env:
            commit_val['commitParams'] = {'buildEnv': {'key1': 'val1', 'key2': 'val2'}}

        return {
            'data': {
                'keywords': [],
                'id': 'dummy_mwu_encoder',
                'name': 'alias_dummy',
                'visibility': 'public',
                'commit': commit_val,
                'package': {
                    'containers': []
                    if self.no_image
                    else ['jinahub/pod.dummy_mwu_encoder'],
                    'download': 'http://hubbleapi.jina.ai/files/dummy_mwu_encoder-v0.zip',
                    'md5': 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f',
                },
            }
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        self._tried_count += 1
        if self._tried_count <= self._fail_count:
            return 500

        return self.response_code


class StatusPostMockResponse:
    def __init__(self, response_code: int = 202, response_error: bool = False):
        self.response_code = response_code
        self.response_error = response_error

    def json(self):
        return {
            "_id": "1e4bebbf22d20",
            "id": "w7qckiqy",
            "ownerUserId": "01044af02b79a",
            "name": "dummy_executor",
            "identifiers": ["w7qckiqy", "dummy_executor"],
            "visibility": "private",
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code

    def iter_lines(self):
        logs = [
            b'{"type":"progress","data":{"sn":212,"dt":28165,"data":{"type":"console","subject":"buildWorkspace"}}}',
            b'{"type":"report","status":"pending"}',
            b'{"type":"report","status":"waiting","task":{"_id":"6316e9ac8e"}}',
            b'{"type":"test","status":"test","task":{"_id":"6316e9ac8e"}}',
            b'{"type":"progress","data":{"sn":213,"dt":28165,"data":{"type":"done","subject":"buildWorkspace"}}}',
            b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}}',
        ]
        if self.response_error:
            logs = [
                b'{"type":"report","status":"failed","message":"async upload error"}',
                b'{"type":"progress","data":{"sn":212,"dt":28165,"data":{"type":"console"}}}',
                b'{"type":"error","message":"async upload error"}',
                b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}}',
            ]

        if self.response_code >= 400:
            logs = [
                b'{"type":"report","status":"failed","message":"async upload error"}',
                b'{"type":"progress","data":{"sn":212,"dt":28165,"data":{"type":"console"}}}',
                b'{"type":"code","message":"AuthenticationRequiredError"}',
                b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}}',
            ]

        return itertools.chain(logs)


@pytest.mark.parametrize('no_cache', [True, False])
@pytest.mark.parametrize('tag', ['v0', None])
@pytest.mark.parametrize('force', [None, 'UUID8'])
@pytest.mark.parametrize('secret', [None, 'test_secret'])
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', [['DOMAIN=github.com', 'DOWNLOAD=download']])
@pytest.mark.parametrize('platform', ['linux/amd64', 'linux/amd64,linux/arm64'])
@pytest.mark.parametrize('verbose', [False, True])
def test_push(
    mocker,
    monkeypatch,
    path,
    mode,
    force,
    secret,
    tag,
    no_cache,
    build_env,
    platform,
    verbose,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path, mode]

    if force:
        _args_list.extend(['--force', force])

    if secret:
        _args_list.extend(['--secret', secret])

    if tag:
        _args_list.extend(['-t', tag])

    if no_cache:
        _args_list.append('--no-cache')

    if build_env:
        for env in build_env:
            _args_list.extend(['--build-env', env])

    if platform:
        _args_list.extend(['--platform', platform])

    if verbose:
        _args_list.append('--verbose')

    args = set_hub_push_parser().parse_args(_args_list)

    with monkeypatch.context() as m:
        m.setattr(hubble, 'is_logged_in', lambda: True)
        image = HubIO(args).push()
        assert type(image['id']) is str

    _, mock_kwargs = mock.call_args_list[0]
    c_type, c_data = cgi.parse_header(mock_kwargs['headers']['Content-Type'])

    assert c_type == 'multipart/form-data'

    form_data = cgi.parse_multipart(
        BytesIO(mock_kwargs['data']), {'boundary': c_data['boundary'].encode()}
    )

    assert 'file' in form_data
    assert 'md5sum' in form_data

    if force and secret:
        assert form_data.get('id') == ['UUID8']
        mock_kwargs['url'] == get_base_url() + '/executor.update'
    else:
        assert form_data.get('id') == ['dummy_executor']
        mock_kwargs['url'] == get_base_url() + '/executor.push'

    if build_env:
        assert form_data['buildEnv'] == [
            '{"DOMAIN": "github.com", "DOWNLOAD": "download"}'
        ]
    else:
        assert form_data.get('buildEnv') is None

    if mode == '--private':
        assert form_data['private'] == ['True']
        assert form_data['public'] == ['False']
    else:
        assert form_data['private'] == ['False']
        assert form_data['public'] == ['True']

    if tag:
        assert form_data['tags'] == ['v0']
    else:
        assert form_data.get('tags') is None

    if no_cache:
        assert form_data['buildWithNoCache'] == ['True']
    else:
        assert form_data.get('buildWithNoCache') is None


@pytest.mark.parametrize(
    'env_variable_consist_error',
    [
        (
            'The `--build-env` parameter key:`{build_env_key}` can only consist of '
            'numbers, upper-case letters and underscore.'
        )
    ],
)
@pytest.mark.parametrize(
    'env_variable_format_error',
    [
        (
            'The `--build-env` parameter: `{build_env}` is in the wrong format. '
            'you can use: `--build-env {build_env}=YOUR_VALUE`.'
        )
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor_fail'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', [['TEST_TOKEN_ccc=ghp_I1cCzUY', 'NO123123']])
@pytest.mark.parametrize('bad_env', ['TEST_TOKEN_ccc'])
def test_push_wrong_build_env(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    env_variable_format_error,
    env_variable_consist_error,
    build_env,
    bad_env,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path, mode]

    if build_env:
        for env in build_env:
            _args_list.extend(['--build-env', env])

    args = set_hub_push_parser().parse_args(_args_list)

    with pytest.raises(Exception) as info:
        HubIO(args).push()

    assert env_variable_format_error.format(build_env=bad_env) in str(
        info.value
    ) or env_variable_consist_error.format(build_env_key=bad_env) in str(info.value)


@pytest.mark.parametrize(
    'requirements_file_need_build_env_error',
    [
        'requirements.txt sets environment variables as follows:`{env_variables_str}` should use `--build-env'
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor_fail'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('requirements_file', ['requirements.txt'])
def test_push_requirements_file_require_set_env_variables(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    requirements_file_need_build_env_error,
    requirements_file,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path, mode]

    args = set_hub_push_parser().parse_args(_args_list)

    requirements_file = os.path.join(exec_path, requirements_file)
    requirements_file_env_variables = get_requirements_env_variables(
        Path(requirements_file)
    )

    with pytest.raises(Exception) as info:
        HubIO(args).push()

    assert requirements_file_need_build_env_error.format(
        env_variables_str=','.join(requirements_file_env_variables)
    ) in str(info.value)


@pytest.mark.parametrize(
    'diff_env_variables_error',
    [
        'requirements.txt sets environment variables as follows:`{env_variables_str}` should use `--build-env'
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor_fail'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', [['TOKEN=ghp_I1cCzUY']])
@pytest.mark.parametrize('bad_env', ['TOKEN=ghp_I1cCzUY'])
def test_push_diff_env_variables(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    diff_env_variables_error,
    build_env,
    bad_env,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path, mode]
    if build_env:
        for env in build_env:
            _args_list.extend(['--build-env', env])

    args = set_hub_push_parser().parse_args(_args_list)

    requirements_file = os.path.join(exec_path, 'requirements.txt')
    requirements_file_env_variables = get_requirements_env_variables(
        Path(requirements_file)
    )
    diff_env_variables = list(
        set(requirements_file_env_variables).difference(set(bad_env))
    )

    with pytest.raises(Exception) as info:
        HubIO(args).push()

    assert diff_env_variables_error.format(
        env_variables_str=','.join(diff_env_variables)
    ) in str(info.value)


@pytest.mark.parametrize(
    'dockerfile, expected_error',
    [
        ('Dockerfile', 'The given Dockerfile `{dockerfile}` does not exist!'),
        (
            '../Dockerfile',
            'The Dockerfile must be placed at the given folder `{work_path}`',
        ),
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
def test_push_wrong_dockerfile(
    mocker, monkeypatch, path, mode, tmpdir, dockerfile, expected_error
):
    dockerfile = str(_resource_dir / path / dockerfile)
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path, mode]

    args = set_hub_push_parser().parse_args(_args_list)
    args.dockerfile = dockerfile

    with pytest.raises(Exception) as info:
        HubIO(args).push()

    assert expected_error.format(dockerfile=dockerfile, work_path=args.path) in str(
        info.value
    )


@pytest.mark.parametrize(
    'response_error',
    ['test error session_id'],
)
@pytest.mark.parametrize(
    'response_image_not_exits_error',
    ['Unknown Error, session_id'],
)
@pytest.mark.parametrize(
    'response_readableMessage_error',
    ['readableMessage session_id'],
)
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', [['DOMAIN=github.com', 'DOWNLOAD=download']])
@pytest.mark.parametrize('response_error_status', ['image_not_exits', 'response_error'])
def test_push_with_error(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    build_env,
    response_error,
    response_image_not_exits_error,
    response_readableMessage_error,
    response_error_status,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(
            response_code=requests.codes.created, response_error=response_error_status
        )

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path, mode]

    if build_env:
        for env in build_env:
            _args_list.extend(['--build-env', env])

    args = set_hub_push_parser().parse_args(_args_list)

    with pytest.raises(Exception) as info:
        HubIO(args).push()

    assert (
        response_error in str(info.value)
        or response_image_not_exits_error in str(info.value)
        or response_readableMessage_error in str(info.value)
    )


@pytest.mark.parametrize('task_id', [None, '6316e9ac8e'])
@pytest.mark.parametrize('verbose', [False, True])
@pytest.mark.parametrize('replay', [False, True])
@pytest.mark.parametrize('is_login', [False, True])
@pytest.mark.parametrize('path', ['dummy_executor'])
def test_status(mocker, monkeypatch, path, verbose, replay, task_id, is_login):

    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers, stream=stream)
        return StatusPostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path]

    if task_id:
        _args_list.extend(['--id', task_id])

    if verbose:
        _args_list.append('--verbose')

    if replay:
        _args_list.append('--replay')

    args = set_hub_status_parser().parse_args(_args_list)

    with monkeypatch.context() as m:
        m.setattr(hubble, 'is_logged_in', lambda: is_login)
        if not task_id:
            m.setattr(
                hubio,
                'get_async_tasks',
                lambda name: [{'_id': '6316e9ac8e'}],
            )
        HubIO(args).status()

    _, mock_kwargs = mock.call_args_list[0]
    c_type, c_data = cgi.parse_header(mock_kwargs['headers']['Content-Type'])

    assert c_type == 'multipart/form-data'

    form_data = cgi.parse_multipart(
        BytesIO(mock_kwargs['data']), {'boundary': c_data['boundary'].encode()}
    )

    if task_id:
        form_data['id'] == task_id

    form_data['verbose'] == bool(verbose)
    form_data['replay'] == bool(replay)


@pytest.mark.parametrize('task_id', [None, '6316e9ac8e'])
@pytest.mark.parametrize('verbose', [False, True])
@pytest.mark.parametrize('replay', [False, True])
@pytest.mark.parametrize('code', [200, 401])
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize(
    'response_error',
    [
        'async upload error',
    ],
)
@pytest.mark.parametrize(
    'response_code_error',
    [
        'AuthenticationRequiredError',
    ],
)
@pytest.mark.parametrize(
    'response_task_id_error',
    [
        'Error: Can\'t get task_id',
    ],
)
def test_status_with_error(
    mocker,
    monkeypatch,
    verbose,
    replay,
    code,
    task_id,
    path,
    response_error,
    response_code_error,
    response_task_id_error,
):

    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers, stream=stream)
        return StatusPostMockResponse(response_code=code, response_error=True)

    monkeypatch.setattr(requests, 'post', _mock_post)

    monkeypatch.setattr(requests, 'get', _mock_post)

    exec_path = str(_resource_dir / path)
    _args_list = [exec_path]

    if task_id:
        _args_list.extend(['--id', task_id])
    else:
        monkeypatch.setattr(
            hubio,
            'get_async_tasks',
            lambda name: [{'_id': '6316e9ac8e'}],
        )

    if verbose:
        _args_list.append('--verbose')

    if replay:
        _args_list.append('--replay')

    with pytest.raises(Exception) as info:
        args = set_hub_status_parser().parse_args(_args_list)
        HubIO(args).status()

    assert (
        response_error in str(info.value)
        or response_code_error in str(info.value)
        or response_task_id_error in str(info.value)
    )


@pytest.mark.parametrize('rebuild_image', [True, False])
@pytest.mark.parametrize('prefer_platform', ['arm64', 'amd64'])
def test_fetch(mocker, monkeypatch, rebuild_image, prefer_platform):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json, headers=headers)
        return FetchMetaMockResponse(response_code=200)

    monkeypatch.setattr(requests, 'post', _mock_post)
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    executor, _ = HubIO(args).fetch_meta(
        'dummy_mwu_encoder',
        None,
        True,
        rebuild_image,
        prefer_platform=prefer_platform,
        force=True,
    )

    assert executor.uuid == 'dummy_mwu_encoder'
    assert executor.name == 'alias_dummy'
    assert executor.tag == 'v0'
    assert executor.image_name == 'jinahub/pod.dummy_mwu_encoder'
    assert executor.md5sum == 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f'

    _, mock_kwargs = mock.call_args_list[0]
    assert mock_kwargs['json']['rebuildImage'] is rebuild_image

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', '', force=True)
    assert executor.tag == 'v0'

    _, mock_kwargs = mock.call_args_list[1]
    assert mock_kwargs['json']['rebuildImage'] is True  # default value must be True

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', 'v0.1', force=True)
    assert executor.tag == 'v0.1'


@pytest.mark.parametrize('rebuild_image', [True, False])
def test_fetch_with_build_env(mocker, monkeypatch, rebuild_image):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return FetchMetaMockResponse(response_code=200, add_build_env=True)

    monkeypatch.setattr(requests, 'post', _mock_post)
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    executor, _ = HubIO(args).fetch_meta(
        'dummy_mwu_encoder', None, rebuild_image=rebuild_image, force=True
    )

    assert executor.uuid == 'dummy_mwu_encoder'
    assert executor.name == 'alias_dummy'
    assert executor.tag == 'v0'
    assert executor.image_name == 'jinahub/pod.dummy_mwu_encoder'
    assert executor.md5sum == 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f'
    assert executor.build_env == ['key1', 'key2']

    _, mock_kwargs = mock.call_args_list[0]
    assert mock_kwargs['json']['rebuildImage'] is rebuild_image

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', '', force=True)
    assert executor.tag == 'v0'

    _, mock_kwargs = mock.call_args_list[1]
    assert mock_kwargs['json']['rebuildImage'] is True  # default value must be True

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', 'v0.1', force=True)
    assert executor.tag == 'v0.1'


def test_fetch_with_no_image(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return FetchMetaMockResponse(response_code=200, no_image=True)

    monkeypatch.setattr(requests, 'post', _mock_post)

    with pytest.raises(RuntimeError) as exc_info:
        HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert exc_info.match('No image found for Executor "dummy_mwu_encoder"')

    executor, _ = HubIO.fetch_meta(
        'dummy_mwu_encoder', tag=None, image_required=False, force=True
    )

    assert executor.image_name is None
    assert mock.call_count == 2


def test_fetch_with_retry(mocker, monkeypatch):
    mock = mocker.Mock()
    mock_response = FetchMetaMockResponse(response_code=200, fail_count=3)

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return mock_response

    monkeypatch.setattr(requests, 'post', _mock_post)

    with pytest.raises(Exception) as exc_info:
        # failing 3 times, so it should raise an error
        HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert exc_info.match('Internal server error')

    mock_response = FetchMetaMockResponse(response_code=200, fail_count=2)

    # failing 2 times, it must succeed on 3rd time
    executor, _ = HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)
    assert executor.uuid == 'dummy_mwu_encoder'

    assert mock.call_count == 6  # mock must be called 3+3


def test_fetch_with_authorization(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers):
        mock(url=url, json=json, headers=headers)
        return FetchMetaMockResponse(response_code=200)

    monkeypatch.setattr(requests, 'post', _mock_post)

    HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert mock.call_count == 1

    _, kwargs = mock.call_args_list[0]

    assert kwargs['headers'].get('Authorization').startswith('token ')


class DownloadMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def iter_content(self, buffer=32 * 1024):
        zip_file = _resource_dir / 'dummy_executor.zip'
        with zip_file.open('rb') as f:
            yield f.read(buffer)

    @property
    def status_code(self):
        return self.response_code


@pytest.mark.parametrize('executor_name', ['dummy_mwu_encoder', None])
@pytest.mark.parametrize('build_env', [['DOWNLOAD', 'DOMAIN'], None])
@pytest.mark.parametrize(
    'executor_uri',
    ['jinaai://user1/dummy_mwu_encoder:tag1', 'jinahub://dummy_mwu_encoder:secret'],
)
def test_pull(mocker, monkeypatch, executor_name, build_env, executor_uri):
    mock = mocker.Mock()

    def _mock_fetch(*args, **kwargs):
        mock(name=args[0])
        return (
            HubExecutor(
                uuid='dummy_mwu_encoder',
                name=executor_name,
                tag='v0',
                image_name='jinahub/pod.dummy_mwu_encoder',
                md5sum=None,
                visibility=True,
                archive_url=None,
                build_env=build_env,
            ),
            False,
        )

    monkeypatch.setattr(HubIO, 'fetch_meta', _mock_fetch)

    def _mock_download(url, stream=True, headers=None):
        mock(url=url)
        return DownloadMockResponse(response_code=200)

    def _mock_head(url):
        from collections import namedtuple

        HeadInfo = namedtuple('HeadInfo', ['headers'])
        return HeadInfo(headers={})

    monkeypatch.setattr(requests, 'get', _mock_download)
    monkeypatch.setattr(requests, 'head', _mock_head)

    def _mock_prettyprint_usage(self, console, *, scheme_prefix, executor_name):
        mock(console=console)
        print('_mock_prettyprint_usage executor_name:', executor_name)
        assert executor_name in executor_uri
        assert executor_uri.startswith(scheme_prefix)

    monkeypatch.setattr(HubIO, '_prettyprint_usage', _mock_prettyprint_usage)

    monkeypatch.setenv('DOWNLOAD', 'download')
    monkeypatch.setenv('DOMAIN', 'github.com')
    args = set_hub_pull_parser().parse_args([executor_uri])
    HubIO(args).pull()


class MockDockerClient:
    def __init__(self, fail_pull: bool = True):
        self.fail_pull = fail_pull
        if not self.fail_pull:
            self.images = {}

    def pull(self, repository: str, stream: bool = True, decode: bool = True):
        if self.fail_pull:
            raise docker.errors.APIError('Failed pulling docker image')
        elif not repository:
            raise docker.errors.NullResource('Resource ID was not provided')
        else:
            yield {}


def test_offline_pull(mocker, monkeypatch, tmpfile):
    mock = mocker.Mock()

    fail_meta_fetch = True
    version = 'v0'
    no_image = False

    @disk_cache_offline(cache_file=str(tmpfile))
    def _mock_fetch(*args, **kwargs):
        mock(name=args[0])
        fixed_tag = args[1] or 'latest'
        image_required = args[2] or True
        if fail_meta_fetch:
            raise urllib.error.URLError('Failed fetching meta')
        elif no_image and image_required:
            raise RuntimeError('No image error')
        else:
            return HubExecutor(
                uuid='dummy_mwu_encoder',
                name='alias_dummy',
                tag=fixed_tag,
                image_name=None
                if (not image_required or no_image)
                else f'jinahub/pod.dummy_mwu_encoder:{fixed_tag}:{version}',
                md5sum=None,
                visibility=True,
                archive_url=None,
            )

    def _gen_load_docker_client(fail_pull: bool):
        def _load_docker_client(obj):
            obj._raw_client = MockDockerClient(fail_pull=fail_pull)
            obj._client = MockDockerClient(fail_pull=fail_pull)

        return _load_docker_client

    args = set_hub_pull_parser().parse_args(
        ['--force', 'jinahub+docker://dummy_mwu_encoder']
    )
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=True)
    )
    monkeypatch.setattr(HubIO, 'fetch_meta', _mock_fetch)

    # Expect failure due to fetch_meta
    with pytest.raises(urllib.error.URLError):
        HubIO(args).pull()

    fail_meta_fetch = False
    # Expect failure due to image pull
    with pytest.raises(AttributeError):
        HubIO(args).pull()

    # expect successful pull
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=False)
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:latest:v0'

    version = 'v1'
    # expect successful forced pull because force == True
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:latest:v1'

    # expect successful pull using cached fetch_meta response and saved image
    fail_meta_fetch = True
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=False)
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:latest:v1'

    args.force_update = False
    fail_meta_fetch = False
    version = 'v2'
    # expect successful but outdated pull because force == False
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:latest:v1'

    # Tagged image should work similarly
    args = set_hub_pull_parser().parse_args(
        ['jinahub+docker://dummy_mwu_encoder/tagged']
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:tagged:v2'

    version = 'v3'
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:tagged:v2'

    no_image = True
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:tagged:v2'

    # Image may be absent, this should throw RuntimeError from fetch_meta
    no_image = True
    args = set_hub_pull_parser().parse_args(
        ['jinahub+docker://dummy_mwu_encoder/tagged2']
    )
    # This exception is raised from fetch_meta
    with pytest.raises(RuntimeError):
        HubIO(args).pull()

    no_image = False
    # The exception should not be cached
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:tagged2:v3'

    version = 'v4'
    args = set_hub_pull_parser().parse_args(
        ['jinahub+sandbox://dummy_mwu_encoder/tagged3']
    )
    # Expect `jinahub+sandbox` not pull-able, but the fetch_meta should succeed and
    # cache should have been saved properly
    # So it must raises ValueError instead of RuntimeError
    with pytest.raises(ValueError):
        HubIO(args).pull()

    no_image = True
    args = set_hub_pull_parser().parse_args(
        ['jinahub+docker://dummy_mwu_encoder/tagged3']
    )
    # The cache for `jinahub+sandbox` should not work for `jinahub+docker`
    # Expect RuntimeError from fetch_meta
    with pytest.raises(RuntimeError):
        HubIO(args).pull()

    # After meta fixed the pull should be successful
    no_image = False
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:tagged3:v4'

    no_image = True
    version = 'v5'
    # Cache should work after first success
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:tagged3:v4'


def test_pull_with_progress():
    import json

    args = set_hub_pull_parser().parse_args(['jinahub+docker://dummy_mwu_encoder'])

    def _log_stream_generator():
        with open(_resource_dir / 'docker_pull.logs') as fin:
            for line in fin:
                if line.strip():
                    yield json.loads(line)

    from rich.console import Console

    console = Console()
    HubIO(args)._pull_with_progress(_log_stream_generator(), console)


@pytest.mark.parametrize('add_dockerfile', ['cpu', 'torch-gpu', 'tf-gpu', 'jax-gpu'])
def test_new_without_arguments(monkeypatch, tmpdir, add_dockerfile):
    from rich.prompt import Confirm, Prompt

    prompts = iter(
        [
            'DummyExecutor',
            tmpdir / 'DummyExecutor',
            add_dockerfile,
            'dummy description',
            'dummy author',
            'dummy tags',
        ]
    )

    def _mock_prompt_ask(*args, **kwargs):
        return next(prompts)

    def _mock_confirm_ask(*args, **kwargs):
        return True

    monkeypatch.setattr(Confirm, 'ask', _mock_confirm_ask)
    monkeypatch.setattr(Prompt, 'ask', _mock_prompt_ask)

    args = set_hub_new_parser().parse_args([])
    HubIO(args).new()
    path = tmpdir / 'DummyExecutor'

    pkg_files = [
        'executor.py',
        'README.md',
        'requirements.txt',
        'config.yml',
    ]

    if add_dockerfile != 'none':
        pkg_files.append('Dockerfile')

    for file in pkg_files:
        assert (path / file).exists()
    for file in [
        'executor.py',
        'README.md',
        'config.yml',
    ]:
        with open(path / file, 'r') as fp:
            assert 'DummyExecutor' in fp.read()


@pytest.mark.parametrize('add_dockerfile', ['cpu', 'torch-gpu', 'tf-gpu', 'jax-gpu'])
@pytest.mark.parametrize('advance_configuration', [True, False])
@pytest.mark.parametrize('confirm_advance_configuration', [True, False])
@pytest.mark.parametrize('confirm_add_docker', [True, False])
def test_new_with_arguments(
    monkeypatch,
    tmpdir,
    add_dockerfile,
    advance_configuration,
    confirm_advance_configuration,
    confirm_add_docker,
):
    from rich.prompt import Confirm

    path = os.path.join(tmpdir, 'DummyExecutor')

    _args_list = [
        '--name',
        'argsExecutor',
        '--dockerfile',
        add_dockerfile,
        '--description',
        'args description',
        '--keywords',
        'args,keywords',
        '--url',
        'args url',
    ]
    temp = []
    _args_list.extend(['--path', path])
    if advance_configuration:
        _args_list.append('--advance-configuration')
    else:
        temp.append(confirm_advance_configuration)

    def _mock_confirm_ask(*args, **kwargs):
        return True

    monkeypatch.setattr(Confirm, 'ask', _mock_confirm_ask)

    args = set_hub_new_parser().parse_args(_args_list)

    HubIO(args).new()
    # path = tmpdir / 'argsExecutor'

    pkg_files = [
        'executor.py',
        'README.md',
        'requirements.txt',
        'config.yml',
    ]

    path = tmpdir / 'DummyExecutor'
    if (advance_configuration or confirm_advance_configuration) and (
        add_dockerfile or confirm_add_docker
    ):
        pkg_files.append('Dockerfile')

    for file in pkg_files:
        assert (path / file).exists()

    for file in ['executor.py', 'README.md', 'config.yml']:
        with open(path / file, 'r') as fp:
            assert 'argsExecutor' in fp.read()

    if advance_configuration or confirm_advance_configuration:
        with open(path / 'config.yml') as fp:
            temp = yaml.load(fp, Loader=yaml.FullLoader)
            assert temp['metas']['name'] == 'argsExecutor'
            assert temp['metas']['description'] == 'args description'
            assert temp['metas']['keywords'] == ['args', 'keywords']
            assert temp['metas']['url'] == 'args url'


class SandboxGetMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def json(self):
        if self.response_code == 200:
            return {
                'code': self.response_code,
                'data': {'host': 'http://test_existing_deployment.com', 'port': 4321},
            }
        else:
            return {'code': self.response_code}

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


class SandboxCreateMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def json(self):
        return {
            'code': self.response_code,
            'data': {'host': 'http://test_new_deployment.com', 'port': 4322},
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


def test_deploy_public_sandbox_existing(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return SandboxGetMockResponse(response_code=200)

    monkeypatch.setattr(requests, "post", _mock_post)

    args = Namespace(
        uses='jinahub+sandbox://dummy_mwu_encoder:dummy_secret',
        uses_with={'foo': 'bar'},
        test_string='text',
        test_number=1,
    )
    host, port = HubIO.deploy_public_sandbox(args)
    assert host == 'http://test_existing_deployment.com'
    assert port == 4321

    _, kwargs = mock.call_args
    assert kwargs['json']['args'] == {
        'uses_with': {'foo': 'bar'},
        'test_number': 1,
        'test_string': 'text',
    }
    assert kwargs['json']['secret'] == 'dummy_secret'


def test_deploy_public_sandbox_create_new(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json, headers=headers)
        if url.endswith('/sandbox.get'):
            return SandboxGetMockResponse(response_code=404)
        else:
            return SandboxCreateMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)

    args = Namespace(uses='jinahub+sandbox://dummy_mwu_encoder')
    host, port = HubIO.deploy_public_sandbox(args)
    assert host == 'http://test_new_deployment.com'
    assert port == 4322


@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('name', ['dummy_executor', None])
def test_list(mocker, monkeypatch, path, name):
    mock = mocker.Mock()

    def _mock_prettyprint_list_usage(self, console, executors, base_path):
        mock(console=console)
        assert base_path is not None
        assert len(executors) == 1
        assert executors[0]['name'] == name

    if name:
        monkeypatch.setattr(
            HubIO, '_prettyprint_list_usage', _mock_prettyprint_list_usage
        )

    exec_path = _resource_dir / path
    args = set_hub_list_parser().parse_args([])

    with monkeypatch.context() as m:
        m.setattr(hubio, 'list_local', lambda: [exec_path / 'latest.dist-info'])
        HubIO(args).list()
