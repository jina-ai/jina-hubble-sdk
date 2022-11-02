import json
import logging
import os
import sys
import uuid
from json import JSONDecodeError
from typing import Dict, Optional, Tuple

from requests import Response

DOMAIN = 'https://api.hubble.jina.ai'
PROTOCOL = 'rpc'
VERSION = 'v2'

__unset_msg__ = '(unset)'
default_logger = logging.getLogger(__name__)
__resources_path__ = os.path.join(
    os.path.dirname(sys.modules['hubble'].__file__), 'resources'
)


def get_base_url():
    """Get the base url based on environment"""

    domain = DOMAIN
    if 'JINA_HUBBLE_REGISTRY' in os.environ:
        domain = os.environ['JINA_HUBBLE_REGISTRY']

    return f'{domain}/{VERSION}/{PROTOCOL}/'


def get_json_from_response(resp: Response) -> dict:
    """
    Get the JSON data from the response.
    If the response isn't JSON, the response information is lost.
    The error message must include the response body and status code.
    """
    try:
        return resp.json()
    except JSONDecodeError as err:
        raise JSONDecodeError(
            f'Response: {resp.text}, status code: {resp.status_code}; {err.msg}',
            err.doc,
            err.pos,
        ) from err


def random_uuid(use_uuid1: bool = False) -> uuid.UUID:
    """
    Get a random UUID.

    :param use_uuid1: Use UUID1 if True, else use UUID4.
    :return: A random UUID.
    """
    return uuid.uuid1() if use_uuid1 else uuid.uuid4()


def get_ci_vendor() -> Optional[str]:
    with open(os.path.join(__resources_path__, 'ci-vendors.json')) as fp:
        all_cis = json.load(fp)
        for c in all_cis:
            if isinstance(c['env'], str) and c['env'] in os.environ:
                return c['constant']
            elif isinstance(c['env'], dict):
                for k, v in c['env'].items():
                    if os.environ.get(k, None) == v:
                        return c['constant']
            elif isinstance(c['env'], list):
                for k in c['env']:
                    if k in os.environ:
                        return c['constant']


def get_full_version() -> Optional[Tuple[Dict, Dict]]:
    """
    Get the version of libraries used in Jina and environment variables.

    :return: Version information and environment variables
    """
    import os
    import platform
    from uuid import getnode

    from hubble import __uptime__
    from hubble import __version__ as __hubble_version__

    try:
        from jina.helper import get_full_version

        metas, env_info = get_full_version()
    except ImportError:
        metas, env_info = {}, {}

    try:
        info = {
            **metas,
            'jina': metas.get('jina') or __unset_msg__,
            'docarray': metas.get('docarray') or __unset_msg__,
            'jcloud': metas.get('jcloud') or __unset_msg__,
            'jina-proto': metas.get('jina-proto') or __unset_msg__,
            'protobuf': metas.get('protobuf') or __unset_msg__,
            'proto-backend': metas.get('proto-backend') or __unset_msg__,
            'grpcio': metas.get('grpcio') or __unset_msg__,
            'pyyaml': metas.get('pyyaml') or __unset_msg__,
            'jina-hubble-sdk': __hubble_version__,
            'python': platform.python_version(),
            'platform': platform.system(),
            'platform-release': platform.release(),
            'platform-version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'uid': getnode(),
            'session-id': str(random_uuid(use_uuid1=True)),
            'uptime': __uptime__,
            'ci-vendor': get_ci_vendor() or __unset_msg__,
            'internal': 'jina-ai'
            in os.getenv('GITHUB_ACTION_REPOSITORY', __unset_msg__),
        }

        full_version = info, env_info
    except Exception as e:
        default_logger.error(str(e))
        full_version = None

    return full_version


def get_request_header() -> Dict:
    """Return the header of request with an authorization token.

    :return: request header
    """
    metas, envs = get_full_version()

    headers = {
        **{f'jinameta-{k}': str(v) for k, v in metas.items()},
        **envs,
    }

    return headers
