from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointsV2(object):
    """All available Hubble API endpoints."""

    create_pat: str = 'user.pat.create'
    list_pats: str = 'user.pat.list'
    delete_pat: str = 'user.pat.delete'
    get_user_info: str = 'user.identity.whoami'
    upload_artifact: str = 'artifact.upload'
    download_artifact: str = 'artifact.getDownloadUrl'
    delete_artifact: str = 'artifact.delete'
    get_artifact_info: str = 'artifact.getDetail'
    list_artifacts: str = 'artifact.list'
