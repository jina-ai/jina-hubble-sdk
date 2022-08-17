#!/usr/bin/env python
import os
import sys
import json

from pathlib import Path
from .client.client import Client  # noqa F401

def deploy_hubble_docker_credential_helper_for(registry: str):
    """
    Deploy hubble docker credential helper for the registry.
    """
    docker_config_file_path = Path(os.path.expanduser('~/.docker/config.json'))
    target_conf = {}
    if docker_config_file_path.exists():
        with docker_config_file_path.open('r+') as f:
            target_conf = json.load(f)
    if ('credHelpers' not in target_conf):
        target_conf['credHelpers'] = {}
    target_conf['credHelpers'][registry] = 'jina-hubble'
    with docker_config_file_path.open('w') as f:
        json.dump(target_conf, f, sort_keys=True, indent=8)


def get_credentials_for(_registry: str):
    """
    Get credentials for the registry.
    """
    c = Client(jsonify=True).token
    token = os.environ.get('JINA_AUTH_TOKEN', c)
    print(json.dumps({'Username': '<token>', 'Secret': token if token else 'anonymous'}, indent=4))


def main():
    """
    Main entry point.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Deploy hubble docker credential helper for the registry.')
    parser.add_argument('action', nargs='?', default='get', help='Action: get, store, erase, or deploy')
    parser.add_argument('--registry', nargs='?', help='The registry to deploy the helper for.')

    args = parser.parse_args()

    # sys.stdin.readlines()

    if args.action == 'get':
        get_credentials_for(args.registry)
        sys.exit(0)
    elif args.action == 'deploy':
        if not args.registry:
            print('Please specify the registry to deploy the helper for.')
            sys.exit(1)
        deploy_hubble_docker_credential_helper_for(args.registry)
        sys.exit(0)
    else:
        sys.exit(1)
