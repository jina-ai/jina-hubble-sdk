"""
The Hubble Python Client
"""
import nest_asyncio

from .client.client import Client  # noqa F401
from .utils.auth import Auth  # noqa F401


def login():
    """This function guide user to browser log-in and get token."""
    nest_asyncio.apply(Auth.login())


def logout():
    """Logout."""
    nest_asyncio.apply(Auth.logout())
