"""
The Hubble Python Client
"""
from .client.client import Client  # noqa F401

__title__ = 'hubble-client-python'
__version__ = '0.1.0'
__summary__ = 'The hubble python sdk.'
__author__ = 'Jina AI'
__email__ = 'hello@jina.ai'


def init():
    """This function should guide user to browser log-in and get token.

    # TODO when user call hubble.init(),
    # TODO open webbrowser and ask user login and get token.
    # TODO if we can get token like this,
    # TODO maybe it's good to set token as env, and load token
    # TODO from env inside BaseClient.
    """
    pass
