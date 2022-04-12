from ..settings import ENVIRONMENT, PROTOCOL, VERSION

HUBBLE_API_PREFIX = 'https://apihubble'
HUBBLE_API_ENDFIX = 'jina.ai'


def get_base_url():
    """Get the base url based on environment"""
    if ENVIRONMENT == 'PRODUCTION':
        env = '.'
    elif ENVIRONMENT == 'STAGING':
        env = 'staging.'
    else:
        raise f'{ENVIRONMENT} is invalid, use either `PRODUCTION` or `STAGING`'
    return (
        HUBBLE_API_PREFIX
        + '.'
        + env
        + HUBBLE_API_ENDFIX
        + '/'
        + VERSION
        + '/'
        + PROTOCOL
        + '/'
    )
