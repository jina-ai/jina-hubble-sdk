import shutil
from typing import Optional, Union

import requests

from .base import BaseClient
from .endpoints import Endpoints


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
            url=self._base_url + Endpoints.create_pat,
            data={'name': name, 'expirationDays': expiration_days},
        )

    def list_personal_access_tokens(self) -> Union[requests.Response, dict]:
        """List all created personal access tokens.

        All expired PATs will be automatically deleted.
        The list function only shows valid PATs.

        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(url=self._base_url + Endpoints.list_pats)

    def delete_personal_access_token(
        self, personal_access_token_id: str
    ) -> Union[requests.Response, dict]:
        """Delete personal access token by id.

        # TODO: bo refactor this, it makes no sense to delete PAT by
        # TODO id while create by name.

        :param personal_access_token_id: Id of the personal access token
          to be deleted.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + Endpoints.delete_pat,
            data={'id': personal_access_token_id},
        )

    def get_user_info(self) -> Union[requests.Response, dict]:
        """Get current logged in user information.

        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(url=self._base_url + Endpoints.get_user_info)

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
            url=self._base_url + Endpoints.upload_artifact,
            data={
                'id': id,
                'metaData': metadata,
                'public': is_public,
            },
            files={'upload_file': open(path, 'rb')},
        )

    def download_artifact(self, id: str) -> Union[requests.Response, dict]:
        """Download artifact from Hubble Artifact Storage to localhost.

        :param id: The id of the artifact to be downloaded.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        # first get download uri.
        resp = self.handle_request(
            url=self._base_url + Endpoints.download_artifact,
            data={'id': id},
        )
        # Second download artifact.
        # TODO: BO fix this with jsonify.
        local_filename = resp.split('/')[-1]
        with requests.get(resp, stream=True) as r:
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        return local_filename

    def delete_artifact(self, id: str) -> Union[requests.Response, dict]:
        """Delete the artifact from Hubble Artifact Storage.

        :param id: The id of the artifact to be deleted.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + Endpoints.delete_artifact,
            data={'id': id},
        )

    def get_artifact_info(self, id: str) -> Union[requests.Response, dict]:
        """Get the metadata of the artifact.

        :param id: The id of the artifact to be deleted.
        :returns: `requests.Response` object as returned value
            or indented json if jsonify.
        """
        return self.handle_request(
            url=self._base_url + Endpoints.get_artifact_info,
            data={'id': id},
        )
