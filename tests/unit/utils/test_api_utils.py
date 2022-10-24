from json import JSONDecodeError

import pytest
from hubble.utils.api_utils import get_json_from_response
from requests import Response


def test_get_json_from_response():
    resp = Response()
    resp.status_code = 502
    resp._content = b'Bad Gateway'

    with pytest.raises(JSONDecodeError) as exc_info:
        get_json_from_response(resp)

    assert 'Response: Bad Gateway, status code: 502;' in str(exc_info.value)
