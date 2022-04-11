from ..settings import ENVIRONMENT, PROTOCAL, VERSION

HUBBLE_API_PREFIX = 'https://apihubble'
HUBBLE_API_ENDFIX = 'jina.ai'


def get_base_url():
    """Get the base url environment"""
    if ENVIRONMENT == 'PRODUCTION':
        return (
            HUBBLE_API_PREFIX
            + '.'
            + HUBBLE_API_ENDFIX
            + '/'
            + VERSION
            + '/'
            + PROTOCAL
            + '/'
        )
    elif ENVIRONMENT == 'STAGING':
        return (
            HUBBLE_API_PREFIX
            + '.'
            + 'staging'
            + '.'
            + HUBBLE_API_ENDFIX
            + '/'
            + VERSION
            + '/'
            + PROTOCAL
            + '/'
        )
    else:
        raise f'{ENVIRONMENT} is invalid, use either `PRODUCTION` or `STAGING`'
