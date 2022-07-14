"""
The Hubble Python Client
"""
import asyncio

from .client.client import Client  # noqa F401
from .utils.auth import Auth  # noqa F401


def login(**kwargs):
    """This function guide user to browser log-in and get token."""
    asyncio.run(Auth.login(**kwargs))


def logout():
    """Logout."""
    asyncio.run(Auth.logout())
