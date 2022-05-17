from hubble.utils.api_utils import get_base_url


def test_get_base_url():
    base_url = get_base_url()
    assert base_url == 'https://api.hubble.jina.ai/v2/rpc/'
