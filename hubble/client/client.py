import json
import shutil
from typing import Optional, Union

import requests

from .base import BaseClient
from .endpoints import EndpointsV2


class Client(BaseClient):
    def create_personal_access_token(
        self, name: str, expiration_days: int = 30
    ) -> Union[requests.Response, dict]:
        """Create a personal access token.

        Personal Access Token (refer as PAT) is same as `api_token`
        where you get from the UI.
        The main difference is that you can set a ``expiration_days``
        for PAT while ``api_token`` becomes invalid as soon as user logout.

        :param name: The name of the personal access token.
        :param expiration_days: Number of days to be valid, by default 30 days.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + EndpointsV2.create_pat,
            data={'name': name, 'expirationDays': expiration_days},
        )

    def list_personal_access_tokens(self) -> Union[requests.Response, dict]:
        """List all created personal access tokens.

        All expired PATs will be automatically deleted.
        The list function only shows valid PATs.

        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(url=self._base_url + EndpointsV2.list_pats)

    def delete_personal_access_token(self, name: str) -> Union[requests.Response, dict]:
        """Delete personal access token by name.

        :param name: Name of the personal access token
          to be deleted.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + EndpointsV2.delete_pat,
            data={'name': name},
        )

    def get_user_info(self) -> Union[requests.Response, dict]:
        """Get current logged in user information.

        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(url=self._base_url + EndpointsV2.get_user_info)

    def upload_artifact(
        self,
        path: str,
        id: Optional[str] = None,
        metadata: Optional[dict] = None,
        is_public=False,
    ) -> Union[requests.Response, dict]:
        """Upload artifact to Hubble Artifact Storage.

        :param path: The full path of the file to be uploaded.
        :param id: Optional value, the id of the artifact.
        :param metadata: Optional value, the metadata of the artifact.
        :param is_public: Optional value, if this artifact is public or not,
          default not public.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + EndpointsV2.upload_artifact,
            data={
                'id': id,
                'metaData': json.dumps(metadata) if metadata else None,
                'public': is_public,
            },
            files={'file': open(path, 'rb')},
        )

    def download_artifact(self, id: str, path: str) -> str:
        """Download artifact from Hubble Artifact Storage to localhost.

        :param id: The id of the artifact to be downloaded.
        :param path: The path and name of the file to be stored in localhost.
        :returns: A str object indicates the download path on localhost.
        """
        # first get download uri.
        resp = self.handle_request(
            url=self._base_url + EndpointsV2.download_artifact,
            data={'id': id},
        )
        # Second download artifact.
        if isinstance(resp, requests.Response):
            resp = resp.json()
        download_url = resp['data']['download']
        with requests.get(download_url, stream=True) as r:
            with open(path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        return path

    def delete_artifact(self, id: str) -> Union[requests.Response, dict]:
        """Delete the artifact from Hubble Artifact Storage.

        :param id: The id of the artifact to be deleted.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + EndpointsV2.delete_artifact,
            data={'id': id},
        )

    def get_artifact_info(self, id: str) -> Union[requests.Response, dict]:
        """Get the metadata of the artifact.

        :param id: The id of the artifact to be deleted.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + EndpointsV2.get_artifact_info,
            data={'id': id},
        )
