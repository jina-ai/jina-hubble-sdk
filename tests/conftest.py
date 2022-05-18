import os

import pytest


@pytest.fixture(autouse=True)
def environment():
    """Test should be performed on staging environment."""
    os.environ['JINA_HUBBLE_REGISTRY'] = 'https://apihubble.staging.jina.ai'
    yield
    del os.environ['JINA_HUBBLE_REGISTRY']
