import requests

from .api_utils import get_domain_url, get_json_from_response
from .config import config


class JSONWebKeySet:
    @staticmethod
    def get_keys(kid: str):
        cached_jwks = JSONWebKeySet.get_keys_from_config()
        matching_jwks = [key for key in cached_jwks if key['kid'] == kid]
        if len(matching_jwks) > 0:
            return matching_jwks
        hubble_jwks = JSONWebKeySet.get_keys_from_hubble()
        matching_jwks = [key for key in hubble_jwks if key['kid'] == kid]
        return matching_jwks

    @staticmethod
    def get_keys_from_config():
        """Get cached JWK list from config file."""
        jwks = config.get('jwks', [])
        return jwks

    @staticmethod
    def get_keys_from_hubble():
        """Get JWK list from hubble API and cache."""
        url = get_domain_url() + 'v2/.well-known/jwks.json'
        response = requests.get(url)
        response.raise_for_status()
        json_response = get_json_from_response(response)
        keys = json_response.get('keys', [])
        config.set('jwks', keys)
        return keys
