"""
The Hubble Python Client
"""
import asyncio

from .client.client import Client  # noqa F401
from .utils.auth import Auth  # noqa F401

__title__ = 'hubble-client-python'
__version__ = '0.1.0'
__summary__ = 'The hubble python sdk.'
__author__ = 'Jina AI'
__email__ = 'hello@jina.ai'


def init():
    """This function guide user to browser log-in and get token."""
    asyncio.run(Auth.login())
