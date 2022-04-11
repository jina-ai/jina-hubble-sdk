from hubble.settings import ENVIRONMENT
from hubble.utils.api_utils import get_base_url


def test_get_base_url():
    base_url = get_base_url()
    if ENVIRONMENT == 'PRODUCTION':
        assert base_url == 'https://apihubble.jina.ai/v2/rpc/'
    elif ENVIRONMENT == 'STAGING':
        assert base_url == 'https://apihubble.staging.jina.ai/v2/rpc/'
