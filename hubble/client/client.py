from typing import Optional
import shutil

import requests

from .endpoints import HubbleAPIEndpoints
from .base import BaseClient


class Client(BaseClient):
    def create_personal_access_token(self, name, expiration_days: int = 30):
        """Create a personal access token."""
        return self.handle_request(
            url=self._base_url + HubbleAPIEndpoints.create_pat,
            data={'name': name, 'expirationDays': expiration_days},
        )

    def list_personal_access_tokens(self):
        """List created personal access tokens."""
        return self.handle_request(url=self._base_url + HubbleAPIEndpoints.list_pats)

    def delete_personal_access_token(self, pat_id: str):
        """Delete personal access token by id."""
        return self.handle_request(
            url=self._base_url + HubbleAPIEndpoints.delete_pat, data={'id': pat_id}
        )

    def get_user_info(self):
        return self.handle_request(
            url=self._base_url + HubbleAPIEndpoints.get_user_info
        )

    def upload_artifact(
        self,
        path: str,
        id: Optional[str] = None,
        metadata: Optional[dict] = None,
        is_public=False,
    ):
        """"""
        return self.handle_request(
            url=self._base_url + HubbleAPIEndpoints.upload_artifact,
            data={
                'id': id,
                'metaData': metadata,
                'public': is_public,
            },
            files={'upload_file': open(path, 'rb')},
        )

    def download_artifact(self, id: str) -> str:
        """"""
        # first get download uri.
        resp = self.handle_request(
            url=self._base_url + HubbleAPIEndpoints.download_artifact,
            data={'id': id},
        )
        # Second download artifact.
        local_filename = resp.split('/')[-1]
        with requests.get(resp, stream=True) as r:
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        return local_filename

    def delete_artifact(self, id: str):
        """"""
        return self.handle_request(
            url=self._base_url + HubbleAPIEndpoints.delete_artifact,
            data={'id': id},
        )

    def get_artifact_info(self, id: str):
        """"""
        return self.handle_request(
            url=self._base_url + HubbleAPIEndpoints.get_artifact_info,
            data={'id': id},
        )
