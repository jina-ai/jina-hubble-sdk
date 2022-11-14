import urllib
import warnings
from pathlib import Path

import pytest
from hubble.executor import helper
from hubble.executor.helper import disk_cache_offline


@pytest.fixture
def dummy_zip_file():
    return Path(__file__).parent / 'dummy_executor.zip'


@pytest.mark.parametrize('plus_scheme', ['', '+docker', '+sandbox'])
def test_parse_hub_legacy_uri(plus_scheme: str):
    result = helper.parse_hub_uri(f'jinahub{plus_scheme}://executor1')
    assert result == (f'jinahub{plus_scheme}', 'executor1', None, None)

    result = helper.parse_hub_uri(f'jinahub{plus_scheme}://executor1/tag1')
    assert result == (f'jinahub{plus_scheme}', 'executor1', 'tag1', None)

    result = helper.parse_hub_uri(f'jinahub{plus_scheme}://executor1:secret1/tag1')
    assert result == (f'jinahub{plus_scheme}', 'executor1', 'tag1', 'secret1')


@pytest.mark.parametrize('plus_scheme', ['', '+docker', '+sandbox'])
def test_parse_hub_uri(plus_scheme: str):
    result = helper.parse_hub_uri(f'jinaai{plus_scheme}://user1/executor1')
    assert result == (f'jinaai{plus_scheme}', 'user1/executor1', None, None)

    result = helper.parse_hub_uri(f'jinaai{plus_scheme}://user1/executor1:tag1')
    assert result == (f'jinaai{plus_scheme}', 'user1/executor1', 'tag1', None)

    result = helper.parse_hub_uri(f'jinaai{plus_scheme}://user1/executor1/:/tag1/')
    assert result == (f'jinaai{plus_scheme}', 'user1/executor1', 'tag1', None)


@pytest.mark.parametrize(
    'uri_path',
    [
        'different-scheme://hello',
        'jinahub://',
        'jinaai://',
        'jinaai://user1',
        'jinaai://user1:tag1',
        'jinaai://user1/MyExecutor:tag1:tag2',
    ],
)
def test_parse_wrong_hub_uri(uri_path):
    with pytest.raises(ValueError) as info:
        helper.parse_hub_uri(uri_path)

    assert f'{uri_path} is not a valid Hub URI' in str(info.value)


def test_replace_secret_of_hub_uri():
    result = helper.replace_secret_of_hub_uri('jinahub://hello', '_secret_')
    assert result == 'jinahub://hello'

    result = helper.replace_secret_of_hub_uri(
        'jinahub://hello:dummy@secret/path', '*secret*'
    )
    assert result == 'jinahub://hello:*secret*/path'

    result = helper.replace_secret_of_hub_uri('hello:magic/world')
    assert result == 'hello:magic/world'


def test_md5file(dummy_zip_file):
    md5sum = helper.md5file(dummy_zip_file)
    assert md5sum == '7ffd1501f24fe5a66dc45883550c2005'


def test_archive_package(tmpdir):
    pkg_path = Path(__file__).parent / 'dummy_executor'

    stream_data = helper.archive_package(pkg_path)
    with open(tmpdir / 'dummy_test.zip', 'wb') as temp_zip_file:
        temp_zip_file.write(stream_data.getvalue())


@pytest.mark.parametrize(
    'package_file',
    [
        Path(__file__).parent / 'dummy_executor.zip',
        Path(__file__).parent / 'dummy_executor.tar',
        Path(__file__).parent / 'dummy_executor.tar.gz',
    ],
)
def test_unpack_package(tmpdir, package_file):
    helper.unpack_package(package_file, tmpdir / 'dummy_executor')


def test_unpack_package_unsupported(tmpdir):
    with pytest.raises(ValueError):
        helper.unpack_package(
            Path(__file__).parent / "dummy_executor.unsupported",
            tmpdir / 'dummy_executor',
        )


def test_install_requirements(monkeypatch):
    monkeypatch.setenv('DOMAIN', 'github.com')
    monkeypatch.setenv('DOWNLOAD', 'download')
    helper.install_requirements(
        Path(__file__).parent / 'dummy_executor' / 'requirements.txt'
    )


@pytest.mark.parametrize(
    'requirement, name, specs, extras',
    [
        ('docarray', 'docarray', [], []),
        ('jina[dev]', 'jina', [], ['dev']),
        ('clip-server==0.3.0', 'clip-server', [('==', '0.3.0')], []),
        ('git+https://github.com/jina-ai/jina.git', 'jina', [], []),
        ('git+https://github.com/jina-ai/jina.git@v0.1', 'jina', [], []),
        (
            'git+https://github.com/jina-ai/jina.git@0.1#egg=jina[dev]',
            'jina',
            [],
            ['dev'],
        ),
        ('http://pypi.python.org/packages/source/p/jina/jina.tar.gz', 'jina', [], []),
    ],
)
def test_parse_requirements(requirement, name, specs, extras):
    from hubble.executor.requirements import parse_requirement

    req_spec = parse_requirement(requirement)

    assert req_spec.project_name == name
    assert list(req_spec.extras) == extras
    assert req_spec.specs == specs


def test_is_requirement_installed(tmpfile):
    with open(tmpfile, 'w') as f:
        f.write('jina==0.0.1\npydatest==0.0.1\nfinefinetuner==0.0.1')
    assert not helper.is_requirements_installed(tmpfile)

    with open(tmpfile, 'w') as f:
        f.write('pytest==0.0.1')
    with pytest.warns(UserWarning, match='VersionConflict') as record:
        assert helper.is_requirements_installed(tmpfile, show_warning=True)
    assert len(record) == 1

    with warnings.catch_warnings(record=True) as record:
        assert helper.is_requirements_installed(tmpfile, show_warning=False)
    assert len(record) == 0

    with open(tmpfile, 'w') as f:
        f.write('jina-awesome-nonexist')
    assert not helper.is_requirements_installed(tmpfile)
    with warnings.catch_warnings(record=True) as record:
        assert not helper.is_requirements_installed(tmpfile, show_warning=True)
    assert len(record) == 1

    with warnings.catch_warnings(record=True) as record:
        assert not helper.is_requirements_installed(tmpfile, show_warning=False)
    assert len(record) == 0

    with open(tmpfile, 'w') as f:
        f.writelines(['pytest'])
    assert helper.is_requirements_installed(tmpfile)


def test_disk_cache(tmpfile):
    raise_exception = True
    result = 1

    # create an invalid cache file
    with open(str(tmpfile), 'w') as f:
        f.write('Oops: db type could not be determined')

    @disk_cache_offline(cache_file=str(tmpfile))
    def _myfunc(force=False) -> bool:
        if raise_exception:
            raise urllib.error.URLError('Failing')
        else:
            return result

    # test fails
    with pytest.raises(urllib.error.URLError) as info:
        _myfunc()
    assert 'Failing' in str(info.value)

    raise_exception = False
    # returns latest, saves result in cache
    assert _myfunc() == (1, False)

    result = 2
    # does not return latest, defaults to cache since force == False
    assert _myfunc() == (1, True)

    # returns latest since force == True
    assert _myfunc(force=True) == (2, False)

    raise_exception = True
    result = 3
    # does not return latest and exception is not raised, defaults to cache
    assert _myfunc(force=True) == (2, True)


def test_replace_env_variables(mocker, monkeypatch):
    monkeypatch.setenv("DOMAIN", 'github.com')
    helper.replace_requirements_env_variables(
        Path(__file__).parent / 'dummy_executor_fail' / 'requirements.txt'
    )


@pytest.mark.parametrize(
    'env_variable_error',
    [
        'The given requirements.txt require environment variables `{var_name}` does not exist!'
    ],
)
@pytest.mark.parametrize('build_env', ['DOMAIN'])
def test_fail_replace_env_variables(mocker, monkeypatch, env_variable_error, build_env):

    with pytest.raises(Exception) as info:
        helper.replace_requirements_env_variables(
            Path(__file__).parent / 'dummy_executor_fail' / 'requirements.txt'
        )
    assert env_variable_error.format(var_name=build_env) in str(info.value)


@pytest.mark.parametrize('tag', ['latest'])
def test_load_config(mocker, tag):
    info_tag = helper.get_tag_from_dist_info_path(
        Path(__file__).parent / 'dummy_executor' / 'latest.dist-info'
    )

    assert info_tag == tag
