# hubble-client-python

Python Hubble SDK.

This package has implemented the hubble auth endpoints and artifact endpoints.

```python
from hubble import Client

client = Client(api_token='your-token', jsonify=True)  # return resp as json rather than requests.Response
# user and auth related
client.get_user_info()  # Get current user information.
client.create_personal_access_token(name='my-pat', expiration_days=30)
client.list_personal_access_tokens()
client.delete_artifact(id='my-pat-id')
# artifact related
client.upload_artifact(path='my-model', is_public=True)
client.get_artifact_info(id='my-artifact-id')
client.download_artifact(id='my-artifact-id', path='my-local-filepath')
client.delete_artifact(id='my-artifact-id')
```