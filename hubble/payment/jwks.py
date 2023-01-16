import requests

from ..utils.api_utils import get_domain_url, get_json_from_response
from ..utils.config import config


class JWKS:
    @staticmethod
    def get_jwks(kid: str):
        cached_jwks = JWKS.get_jwks_from_config()
        matching_jwks = [key for key in cached_jwks if key['kid'] == kid]
        if len(matching_jwks) > 0:
            return matching_jwks
        hubble_jwks = JWKS.get_jwks_from_hubble()
        matching_jwks = [key for key in hubble_jwks if key['kid'] == kid]
        return matching_jwks

    @staticmethod
    def get_jwks_from_config():
        """Get cached JWK list from config file."""
        jwks = config.get('jwks')
        return jwks

    @staticmethod
    def get_jwks_from_hubble():
        """Get JWK list from hubble API and cache."""
        url = get_domain_url() + 'v2/.well-known/jwks.json'
        response = requests.get(url)
        response.raise_for_status()
        json_response = get_json_from_response(response)
        keys = json_response.get('keys', [])
        config.set('jwks', keys)
        return keys
