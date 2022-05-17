import os

DOMAIN = 'https://api.hubble.jina.ai'
PROTOCOL = 'rpc'
VERSION = 'v2'


def get_base_url():
    """Get the base url based on environment"""

    domain = DOMAIN
    if 'JINA_HUBBLE_REGISTRY' in os.environ:
        domain = os.environ['JINA_HUBBLE_REGISTRY']

    return f'{domain}/{VERSION}/{PROTOCOL}/'
