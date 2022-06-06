"""
The Hubble Python Client
"""
import asyncio

import nest_asyncio

from .client.client import Client  # noqa F401
from .utils.auth import Auth, _is_in_colab  # noqa F401

nest_asyncio.apply()
if _is_in_colab():
    __import__('IPython').embed()


def login():
    """This function guide user to browser log-in and get token."""
    asyncio.run(Auth.login())


def logout():
    """Logout."""
    asyncio.run(Auth.logout())
