"""
The Hubble Python Client
"""
import asyncio

from .client.client import Client  # noqa F401
from .utils.auth import Auth  # noqa F401

__version__ = '0.1.3'


def login():
    """This function guide user to browser log-in and get token."""
    asyncio.run(Auth.login())
