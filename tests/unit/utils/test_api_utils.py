import os

from hubble.utils.api_utils import get_base_url


def test_get_base_url():
    base_url = get_base_url()
    domain = os.environ['JINA_HUBBLE_REGISTRY']
    assert base_url == f'{domain}/v2/rpc/'
