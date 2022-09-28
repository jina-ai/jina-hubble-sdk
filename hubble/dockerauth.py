#!/usr/bin/env python
import json
import os
import sys
from pathlib import Path

from .client.client import Client  # noqa F401


def deploy_hubble_docker_credential_helper_for(*registries: str):
    """
    Deploy hubble docker credential helper for the registry.
    """
    docker_config_dir = os.environ.get('DOCKER_CONFIG', '~/.docker')
    docker_config_dir_path = Path(os.path.expanduser(docker_config_dir))
    docker_config_file_path = Path(
        os.path.expanduser(docker_config_dir + '/config.json')
    )
    target_conf = {}

    if docker_config_file_path.exists():
        with docker_config_file_path.open('r+') as f:
            target_conf = json.load(f)
    if 'credHelpers' not in target_conf:
        target_conf['credHelpers'] = {}
    for registry in registries:
        target_conf['credHelpers'][registry] = 'jina-hubble'

    if not docker_config_dir_path.exists():
        docker_config_dir_path.mkdir(parents=True, exist_ok=True)

    with docker_config_file_path.open('w') as f:
        json.dump(target_conf, f, sort_keys=True, indent=2)
        f.write('\n')


def get_credentials_for(_registry: str):
    """
    Get credentials for the registry.
    """
    token = Client(jsonify=True).token
    username = os.environ.get('HUBBLE_DOCKER_AUTH_OVERRIDE_USERNAME', '<token>')
    secret = os.environ.get('HUBBLE_DOCKER_AUTH_OVERRIDE_SECRET', token)

    sys.stdout.write(
        json.dumps(
            {'Username': username, 'Secret': secret if secret else 'anonymous'},
            indent=2,
        )
    )
    sys.stdout.write('\n')


def auto_deploy_hubble_docker_credential_helper():
    """
    Discover then deploy hubble docker credential helper for internal registries.
    """
    client = Client(jsonify=True)
    registries = client.list_internal_docker_registries().get('data', [])
    deploy_hubble_docker_credential_helper_for(*registries)


def main():
    """
    Main entry point.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Hubble docker credential helper for the registry.'
    )
    parser.add_argument(
        'action', nargs='?', default='get', help='Action: get, store, erase, or deploy'
    )
    parser.add_argument(
        'registry', nargs='?', help='The registry to deploy helper for.'
    )

    args = parser.parse_args()

    # sys.stdin.readlines()

    if args.action == 'get':
        get_credentials_for(args.registry)
        sys.exit(0)
    elif args.action == 'deploy':
        if not args.registry:
            auto_deploy_hubble_docker_credential_helper()
            sys.exit(1)
        deploy_hubble_docker_credential_helper_for(args.registry)
        sys.exit(0)
    else:
        sys.exit(1)
